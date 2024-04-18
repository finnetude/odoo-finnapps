from odoo import models, fields, api, _
from odoo.exceptions import  ValidationError
import datetime
from calendar import monthrange

import logging as log # log.warning("============================= function {}".format())

REPORTS_TYPE ={
        'bilan_actif':['bilan_actif'],
        'bilan_passif':['bilan_passif'],
        'compte_resultat':['compte_resultat'],
        'tableau_flux_tresorerie':['tableau_flux_tresorerie'],
        'stock':['stock_1','stock_2'],
        'charge':['charge_1','charge_2'],
        'amo_inv':['amo_inv_1','amo_inv_2'],
        'cess_prov':['cess_prov_1','cess_prov_2'],
        'perte_val':['perte_val_1','perte_val_2'],
        'result':['result'],
        'tab':['tab_1','tab_2'],
        'commission':['commission_1','commission_2']
        
        }

REPORTS_NAME ={
        'bilan_actif':'Bilan (ACTIF)',
        'bilan_passif':'Bilan (PASSIF)',
        'compte_resultat':'Compte de résultat',
        'tableau_flux_tresorerie':'Tableau des flux de trésorerie',
        'stock':'Stocks (1-2)',
        'charge':'Charges/prod. (3-4)',
        'amo_inv':'Amo./Inv. (5-6)',
        'cess_prov':'Cess./Prov. (7-8)',
        'perte_val':'Perte val. (8/1-8/2)',
        'result':'D. résultat (9)',
        'tab':'Tab. (10-11)',
        'commission':'Hon./TAP (12-13)'
        
        }

class FinnLiasseFiscaleReport(models.Model):
    _name = "finn.liasse.fiscale.report"
    _description = "Rapport de la liasse fiscale"

# ====================================== DEFAULT ========================================
    # @api.model
    # def default_get(self, fields_list):
    #     res = super(FinnLiasseFiscaleReport, self).default_get(fields_list)
    #     return res

# ====================================== CHAMPS ========================================

    name = fields.Char('Désignation', readonly=True, required=True, copy=False, compute='_compute_name')

    company_id = fields.Many2one('res.company', string='Société', readonly=True, default=lambda self: self.env.company.id)

    state = fields.Selection(string='State', selection=[('draft', 'Brouillon'), ('lock', 'Verouillé')], default='draft',)
    
    type_report = fields.Char(string='Type de rapport', readonly=True, required=True)

    lock_date = fields.Datetime('Date de verrouillage', readonly=True)

    exercice_id = fields.Many2one('finn.exercice', string='Exercice', compute='_compute_exercice', store=True)

    liasse_fiscal_id = fields.Many2one('finn.liasse.fiscale', string='Liasse fiscal', readonly=True)

    switch_button = fields.Boolean(default=False)

# ====================================== CHAMPS DES RAPPORTS ========================================

    # Bilan (actif)
    line_bilan_actif_ids = fields.One2many('finn.liasse.fiscale.line','inv_bilan_actif_id')

    # Bilan (passif)
    line_bilan_passif_ids = fields.One2many('finn.liasse.fiscale.line','inv_bilan_passif_id')

    # Compte de résultat
    line_compte_resultat_ids = fields.One2many('finn.liasse.fiscale.line','inv_compte_resultat_id')

    # Tableau des flux de trésorerie
    line_tableau_flux_tresorerie_ids = fields.One2many('finn.liasse.fiscale.line','inv_tableau_flux_tresorerie_id')

    # 1/ Tableau des mouvements des stocks
    line_stock_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_stock_1_id')

    # 2/ Tableau de la fluctuation de la production stockée
    line_stock_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_stock_2_id')

    # 3/ Charges de personnel, impôts, taxes et versements assimilés, autres services
    line_charge_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_charge_1_id')

    # 4/ Autres charges et produits opérationnels
    line_charge_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_charge_2_id')

    # 5/ Tableau des amortissements et pertes de valeurs
    line_amo_inv_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_amo_inv_1_id')

    # 6/ Tableau des immobilisations créées ou acquises au cours de l’exercice
    line_amo_inv_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_amo_inv_2_id')

    # 7/ Tableau des immobilisations cédées (plus ou moins value) au cours de l’exercice
    line_cess_prov_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_cess_prov_1_id')

    # 8/ Tableau des provisions et pertes de valeurs
    line_cess_prov_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_cess_prov_2_id')

    # 8/1 Relevé des pertes de valeurs sur créances
    line_perte_val_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_perte_val_1_id')

    # 8/2 Relevé des pertes de valeurs sur actions et parts sociales
    line_perte_val_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_perte_val_2_id')

    # 9/ Tableau de détermination du résultat fiscal
    line_result_ids = fields.One2many('finn.liasse.fiscale.line','inv_result_id')

    # 10/ Tableau d’affectation du résultat et des réserves (N-1)
    line_tab_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_tab_1_id')

    # 11/ Tableau des participations (filiales et entités associées)
    line_tab_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_tab_2_id')

    # 12/ Commissions et courtages, redevances, honoraires, sous-traitance, rémunérations diverses et frais de siège
    line_commission_1_ids = fields.One2many('finn.liasse.fiscale.line','inv_commission_1_id')

    # 13/ Taxe sur l’activité professionnelle
    line_commission_2_ids = fields.One2many('finn.liasse.fiscale.line','inv_commission_2_id')
    
    
    

# ====================================== COMPUTES ========================================

    @api.depends('liasse_fiscal_id','type_report')
    def _compute_name(self):
        for record in self:
            if record.liasse_fiscal_id.exercice_id:
                record.name = "{} ({})".format(REPORTS_NAME[record.type_report], record.liasse_fiscal_id.exercice_id.name)
            else:
                record.name = "Nouveau"

    @api.depends('liasse_fiscal_id')
    def _compute_exercice(self):
        for record in self:
            if record.liasse_fiscal_id.exercice_id:
                record.exercice_id = record.liasse_fiscal_id.exercice_id.id
            else:
                record.exercice_id = False


# ====================================== OVERRIDE ========================================
    @api.model
    def create(self, vals):
        result = super(FinnLiasseFiscaleReport,self).create(vals)

        for report in REPORTS_TYPE[result.type_report]:
            type_report_id = self.env['finn.liasse.fiscale.type'].search([('code','=',report)])

            if report in ['cess_prov_1','perte_val_1','perte_val_2','tab_2','commission_1','commission_2']:
                self.write({'line_{}_ids'.format(report):False,})
                return result

            line_ids = {}
            create_line = []
            for line in type_report_id.line_ids:
                create_line.append((0,0,{
                    'name': line.name,
                    'code': line.code,
                    'display_type': line.display_type,
                }))
                line_ids['line_{}_ids'.format(report)] = create_line or False
            result.update(line_ids)
        return result

# ====================================== BOUTONS ========================================

    def to_draft(self):
        if self.liasse_fiscal_id.state == 'lock':
            raise ValidationError(_('Vous ne pouvez pas remettre en brouillon ce rapport si la liasse fiscal est vérouillée'))
        self.state = "draft"
        self.lock_date = False

    def to_lock(self):
        self.state = "lock"
        self.lock_date = datetime.datetime.now()
        self.switch_button = False

    def reinitialisation(self):
        for report in REPORTS_TYPE[self.type_report]:
            type_report_id = self.env['finn.liasse.fiscale.type'].search([('code','=',report)])

            self.write({'line_{}_ids'.format(report):False,})
            
            if report in ['cess_prov_1','perte_val_1','perte_val_2','tab_2','commission_1','commission_2']:
                return

            create_line = []
            for line in type_report_id.line_ids:
                create_line.append((0,0,{
                    'name': line.name,
                    'code': line.code,
                    'display_type': line.display_type,
                }))

            self.write({'line_{}_ids'.format(report): create_line or False,
                        'switch_button': False})

    def calculate_line(self):
        for report in REPORTS_TYPE[self.type_report]:
            type_report_id = self.env['finn.liasse.fiscale.type'].search([('code','=',report)])

            if report in ['cess_prov_1','perte_val_1','perte_val_2','tab_2','commission_1','commission_2']:
                self.write({'line_{}_ids'.format(report):False,})
        
            old_exercice = self.search_old_exercice(self.exercice_id)

            create_line = []
            for line in type_report_id.line_ids:
                # (le type du rapport, la ligne de configuration, l'exercice utilisé, l'ancien exercice)
                cal_tuple = getattr(self, 'calcule_{}'.format(report))(report, line, self.exercice_id, old_exercice)
                # cal_tuple = ('date_line','name','designation_col_one','designation_col_two','amount_col_one','amount_col_two','amount_col_three','amount_col_four','amount_col_five','amount_col_six','mode create or wirte')
                report_line = self.env['finn.liasse.fiscale.line'].search([('inv_{}_id'.format(report),'=',self.id),('code','=',line.code)], limit=1)

                if cal_tuple[10] == 'write':
                    report_line.write({
                        'date_line': cal_tuple[0],
                        'name': line.name or cal_tuple[1],
                        'designation_col_one': cal_tuple[2],
                        'designation_col_two': cal_tuple[3],
                        'amount_col_one': cal_tuple[4],
                        'amount_col_two': cal_tuple[5],
                        'amount_col_three': cal_tuple[6],
                        'amount_col_four': cal_tuple[7],
                        'amount_col_five': cal_tuple[8],
                        'amount_col_six': cal_tuple[9],
                        })

                if cal_tuple[10] == 'create':
                    create_line.append((0,0,{
                        'code': line.code,
                        'display_type': line.display_type,
                        'date_line': cal_tuple[0],
                        'name': line.name or cal_tuple[1],
                        'designation_col_one': cal_tuple[2],
                        'designation_col_two': cal_tuple[3],
                        'amount_col_one': cal_tuple[4],
                        'amount_col_two': cal_tuple[5],
                        'amount_col_three': cal_tuple[6],
                        'amount_col_four': cal_tuple[7],
                        'amount_col_five': cal_tuple[8],
                        'amount_col_six': cal_tuple[9],
                    }))
                
            if create_line:
                self.write({'line_{}_ids'.format(report): create_line})

            self.write({'switch_button': True})

    def recalculate_line(self):     
        self.calculate_line()

# ====================================== FONCTIONS ========================================

    def amount_account_move_line(self, accounts, exercice):
        periodes = self.env[('finn.periode')].search([('exercice_id','=',exercice.id),('is_closing_date','!=',True)])
        records = self.env['account.move.line'].search([('account_id','in', accounts.ids),('period_id','in',periodes.ids),('parent_state','=','posted')])
        total_debit = sum((records).mapped('debit'))
        total_credit = sum((records).mapped('credit'))
        total_balance = total_debit - total_credit
        return total_debit, total_credit, total_balance

    def search_old_exercice(self, exercice):
        date_end = exercice.date_from - datetime.timedelta(days=1)
        old_exercice = exercice.search([('date_to','=',date_end)],limit=1)
        return old_exercice

# ====================================== FONCTION CALCULE ========================================
    # cal_tuple = ('date_line','name','designation_col_one','designation_col_two','amount_col_one','amount_col_two','amount_col_three','amount_col_four','amount_col_five','amount_col_six','mode create or wirte')

    def _calcul_load_account(self, definition, liste_account, exercice, type_account):
        account_include = account_exclude = self.env['account.account']
        accounts = self.env['account.account'].search([]).mapped('code')

        acc_list_include = liste_account
        if acc_list_include:
            liste_include = []
            for a in acc_list_include:
                liste_include += [n for n in accounts if str(n).startswith(a)]
            account_include = self.env['account.account'].search([('code','in',liste_include)])
        
        acc_list_exclude = definition['except']
        if acc_list_exclude :
            liste_exclude = []
            for a in acc_list_exclude:
                liste_exclude += [n for n in accounts if str(n).startswith(a)]

            account_exclude = self.env['account.account'].search([('code','in',liste_exclude)])

        accounts = account_include - account_exclude
        periodes = self.env[('finn.periode')].search([('exercice_id','=',exercice.id),('is_closing_date','!=',True)])
        move_lines = self.env['account.move.line'].search([
            ('account_id','in', accounts.ids),
            ('period_id','in',periodes.ids),
            ('parent_state','=','posted')
            ])

        som_cpt = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))

        if type_account == 'S':
            return som_cpt
        if type_account == 'D':
            return som_cpt if som_cpt > 0 else 0  
        if type_account == 'C':
            return som_cpt if som_cpt < 0 else 0

    def _calcule_totale(self, type_report, line):
        somme_col_1, somme_col_2, somme_col_3, somme_col_4, somme_col_5, somme_col_6 = [0, 0, 0, 0, 0, 0]
        for liste_report_line in eval(line.definition):
            sign, code_line = liste_report_line.split(':')
            report_line = self.env['finn.liasse.fiscale.line'].search([('inv_{}_id'.format(type_report),'=',self.id),('code','=',code_line)])
            res_sign = 1 if sign == '+' else -1
            somme_col_1 += res_sign * report_line.amount_col_one
            somme_col_2 += res_sign * report_line.amount_col_two
            somme_col_3 += res_sign * report_line.amount_col_three
            somme_col_4 += res_sign * report_line.amount_col_four
            somme_col_5 += res_sign * report_line.amount_col_five
            somme_col_6 += res_sign * report_line.amount_col_six
        return (False,False,False,False,somme_col_1,somme_col_2,somme_col_3,somme_col_4,somme_col_5,somme_col_6,'write')

    def calcule_bilan_actif(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        
        if line.display_type == 'calcule':
            brut, old_brut, amort_prov, old_amort_prov, net, old_net= [0,0,0,0,0,0]
            
            liste_account_S = liste_account_D = liste_account_C = []
            for load_account in definition['brut']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            brut += self._calcul_load_account(definition['brut'], liste_account_S, exercice, type_account)

            if old_exercice:
                old_brut += self._calcul_load_account(definition['brut'], liste_account_S, old_exercice, type_account)
            else:
                old_brut = 0

            liste_account_S = liste_account_D = liste_account_C = []
            for load_account in definition['amort_prov']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            amort_prov += self._calcul_load_account(definition['amort_prov'], liste_account_S, exercice, type_account)

            if old_exercice:
                old_amort_prov += self._calcul_load_account(definition['amort_prov'], liste_account_D, old_exercice, type_account)
            else:
                old_amort_prov = 0

            net = brut - amort_prov
            old_net = old_brut - old_amort_prov
            return (False,False,False,False,brut,amort_prov,net,old_net,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_bilan_passif(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)

        if line.display_type == 'calcule':
            net, old_net= [0,0]
            liste_account_S = liste_account_D = liste_account_C = []
            if not definition['net']['load']:
                return (False,False,False,False,net,old_net,0,0,0,0,'write')

            for load_account in definition['net']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            net += self._calcul_load_account(definition['net'], liste_account_S, exercice, type_account)

            if old_exercice:
                old_net += self._calcul_load_account(definition['net'], liste_account_S, old_exercice, type_account)
            else:
                old_net = 0

            return (False,False,False,False,net,old_net,0,0,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_compte_resultat(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        if line.display_type == 'calcule':
            debit, credit, old_debit, old_credit= [0,0,0,0]
            liste_account_S = liste_account_D = liste_account_C = []

            for load_account in definition['debit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            debit += self._calcul_load_account(definition['debit'], liste_account_D, exercice, 'D')

            for load_account in definition['credit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            credit += self._calcul_load_account(definition['credit'], liste_account_C, exercice, 'C')

            if old_exercice:
                old_debit += self._calcul_load_account(definition['debit'], liste_account_D, old_exercice, 'D')
                old_credit += self._calcul_load_account(definition['credit'], liste_account_C, old_exercice, 'C')
            else:
                old_debit = 0
                old_credit = 0

            return (False,False,False,False,debit,credit,old_debit,old_credit,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_tableau_flux_tresorerie(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_stock_1(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        
        if line.display_type == 'calcule':
            debit, old_debit, credit, old_credit, net, old_net= [0,0,0,0,0,0]
            liste_account_S = liste_account_D = liste_account_C = []

            for load_account in definition['debit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            debit += self._calcul_load_account(definition['debit'], liste_account_S, exercice, 'S')
            debit += self._calcul_load_account(definition['debit'], liste_account_C, exercice, 'C')
            debit += self._calcul_load_account(definition['debit'], liste_account_D, exercice, 'D')

            if old_exercice:
                old_debit += self._calcul_load_account(definition['debit'], liste_account_S, old_exercice, 'S')
                old_debit += self._calcul_load_account(definition['debit'], liste_account_C, old_exercice, 'C')
                old_debit += self._calcul_load_account(definition['debit'], liste_account_D, old_exercice, 'D')
            else:
                old_debit = 0

            for load_account in definition['credit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            credit += self._calcul_load_account(definition['credit'], liste_account_S, exercice, 'S')
            credit += self._calcul_load_account(definition['credit'], liste_account_C, exercice, 'C')
            credit += self._calcul_load_account(definition['credit'], liste_account_D, exercice, 'D')

            if old_exercice:
                old_credit += self._calcul_load_account(definition['credit'], liste_account_S, old_exercice, 'S')
                old_credit += self._calcul_load_account(definition['credit'], liste_account_C, old_exercice, 'C')
                old_credit += self._calcul_load_account(definition['credit'], liste_account_D, old_exercice, 'D')
            else:
                old_credit = 0

            net = debit - credit
            old_net = old_debit - old_credit
            return (False,False,False,False,net,debit,credit,old_net,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_stock_2(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        
        if line.display_type == 'calcule':
            debit, old_debit, credit, old_credit, net, old_net= [0,0,0,0,0,0]
            liste_account_S = liste_account_D = liste_account_C = []

            for load_account in definition['debit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            debit += self._calcul_load_account(definition['debit'], liste_account_S, exercice, 'S')
            debit += self._calcul_load_account(definition['debit'], liste_account_C, exercice, 'C')
            debit += self._calcul_load_account(definition['debit'], liste_account_D, exercice, 'D')

            if old_exercice:
                old_debit += self._calcul_load_account(definition['debit'], liste_account_S, old_exercice, 'S')
                old_debit += self._calcul_load_account(definition['debit'], liste_account_C, old_exercice, 'C')
                old_debit += self._calcul_load_account(definition['debit'], liste_account_D, old_exercice, 'D')
            else:
                old_debit = 0

            for load_account in definition['credit']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)
                if type_account == 'D':
                    liste_account_D.append(code_account)
                if type_account == 'C':
                    liste_account_C.append(code_account)

            credit += self._calcul_load_account(definition['credit'], liste_account_S, exercice, 'S')
            credit += self._calcul_load_account(definition['credit'], liste_account_C, exercice, 'C')
            credit += self._calcul_load_account(definition['credit'], liste_account_D, exercice, 'D')

            if old_exercice:
                old_credit += self._calcul_load_account(definition['credit'], liste_account_S, old_exercice, 'S')
                old_credit += self._calcul_load_account(definition['credit'], liste_account_C, old_exercice, 'C')
                old_credit += self._calcul_load_account(definition['credit'], liste_account_D, old_exercice, 'D')
            else:
                old_credit = 0

            return (False,False,False,False,debit,credit,old_debit,old_credit,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_charge_1(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        
        if line.display_type == 'calcule':
            net = 0
            liste_account_S = []

            for load_account in definition['net']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)

            net += self._calcul_load_account(definition['net'], liste_account_S, exercice, 'S')

            return (False,False,False,False,net,0,0,0,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_charge_2(self, type_report, line, exercice, old_exercice):
        definition = eval(line.definition)
        
        if line.display_type == 'calcule':
            net = 0
            liste_account_S = []

            for load_account in definition['net']['load']:
                code_account, type_account = load_account.split(':')
                if type_account == 'S':
                    liste_account_S.append(code_account)

            net += self._calcul_load_account(definition['net'], liste_account_S, exercice, 'S')

            return (False,False,False,False,net,0,0,0,0,0,'write')
        if line.display_type == 'total':
            return self._calcule_totale(type_report, line)

    def calcule_amo_inv_1(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_amo_inv_2(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_cess_prov_1(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    def calcule_cess_prov_2(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_perte_val_1(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    def calcule_perte_val_2(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    def calcule_result(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_tab_1(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'write')

    def calcule_tab_2(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    def calcule_commission_1(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    def calcule_commission_2(self, type_report, line, exercice, old_exercice):
        return (False,False,False,False,0,0,0,0,0,0,'create')

    
    
# ====================================== ACTION PRINT ======================================== 

    def action_report(self):
        try:
            action = self.env.ref('finnapps_liasse_fiscale_dz.action_{}_report'.format(self.type_report))
            return action.report_action(self)
        except:
            ValidationError(_("L'imprission de ce rapport n'existe pas"))