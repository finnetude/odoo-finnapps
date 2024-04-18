from odoo import fields, models, api, _
from odoo.exceptions import  ValidationError
import odoo.addons.decimal_precision as dp

from calendar import monthrange
import datetime
import ast

# ====================================== CONSTANTES ========================================

class ReportG50(models.Model):
    _name = 'report.g50'
    _description = 'Rapport G50'

# ====================================== DEFAULT ========================================
# ====================================== CHAMP ========================================

    name = fields.Char(compute='_compute_name', store=True)

    state = fields.Selection(string='State', selection=[('draft', 'Brouillon'), ('lock', 'Verouillé')], default='draft',)

    switch_button = fields.Boolean(default=False)

    bp = fields.Char(string='BP')

    # Exercice et période
    exercice_id = fields.Many2one('finn.exercice', 'Exercice', required=True)

    type = fields.Selection([('1', 'Mensuel'),('2', 'Trimestriel')], 'Type de déclaration',required=True)

    month = fields.Selection([
        ('1', 'Janvier'),
         ('2', 'Février'),
         ('3', 'Mars'),
         ('4', 'Avril'),
         ('5', 'Mai'),
         ('6', 'Juin'),
         ('7', 'Juillet'),
         ('8', 'Août'),
         ('9', 'Septembre'),
         ('10', 'Octobre'),
         ('11', 'Novembre'),
         ('12', 'Décembre')],
        'Mois')

    trimestre = fields.Selection([
        ('1', 'Premier'),
        ('2', 'Deuxième'),
        ('3', 'Troisième'),
        ('4', 'Quatrième')],
        'Trimestre')
    
    # Localisation
    company_id = fields.Many2one('res.company', 'Société', required=True, readonly=True, default=lambda self: self.env.user.company_id.id,)

    state_id = fields.Many2one('res.country.state', 'Direction des impôts de la wilaya', required=True, default=lambda self: self.env.user.company_id.state_id.id)

    state_inspection_id = fields.Many2one('res.country.state', 'Inspection des impôts', required=True, default=lambda self: self.env.user.company_id.state_id.id)

    commune_recette_id = fields.Many2one('finn.res.country.state.commune', 'Recette des impôts', required=True, default=lambda self: self.env.user.company_id.commune_id.id)

    commune_id = fields.Many2one('finn.res.country.state.commune', 'Commune', required=True, default=lambda self: self.env.user.company_id.commune_id.id)

    # Configuration
    configuration_id = fields.Many2one('config.g50', required=True)

    move_id = fields.Many2many('account.move',string='Factures')
    
    move_g50_id = fields.One2many('account.move.g50','report_id')
    
    with_move_entry = fields.Selection([('only_invoices', 'Uniquement les factures'), ('full_move', 'Toutes les pièces')], string="Récupérer", default="only_invoices")

    # Autre
    lock_date = fields.Datetime('Date de verrouillage', readonly=True)

    date = fields.Date(string="Date d'impression")

    user_id = fields.Many2one('res.users', 'Responsable', default=lambda self: self.env.user.id)
    
# ====================================== CHAMP TABLEAU ========================================

    line_tap_ids = fields.One2many('report.g50.line', 'report_tap_id')

    line_ibs_ids = fields.One2many('report.g50.line', 'report_ibs_id')

    line_irg_ids = fields.One2many('report.g50.line', 'report_irg_id')

    line_timbre_ids = fields.One2many('report.g50.line', 'report_timbre_id')

    line_autre_ids = fields.One2many('report.g50.line', 'report_autre_id')

    line_tva_9_ids = fields.One2many('report.g50.line', 'report_tva_9_id')

    line_tva_19_ids = fields.One2many('report.g50.line', 'report_tva_19_id')

    line_deduction_ids = fields.One2many('report.g50.line', 'report_deduction_id')

    line_tva_p_ids = fields.One2many('report.g50.line','report_tva_p_id')

# ====================================== OVERIDE ========================================
    @api.model
    def create(self, vals):
        result = super(ReportG50,self).create(vals)
        tabs = ['tap','ibs','irg','timbre','autre','tva_9','tva_19','deduction','tva_p']
        for tab in tabs:
            line_ids = {}
            create_line = []
            for line in result.configuration_id['line_{}_ids'.format(tab)]:
                create_line.append((0,0,{
                    'code': line.code,
                    'name':line.name,
                    'ratio': line.ratio.id,
                    'type_line': line.type_line,
                 }))
                line_ids['line_{}_ids'.format(tab)] = create_line or False
            result.update(line_ids)
        return result

    def unlink(self):
        if self.state == 'lock':
            raise ValidationError(_("Vous ne pouvez pas supprimer une rapport vérouillé !"))
        super(ReportG50, self).unlink()

# ====================================== ONCHANGE ========================================
# ====================================== COMPUTE ========================================

    def _get_default_name(self):
        name = ''
        if self.type == "1":
            if self.month:
                name = dict(self._fields['month'].selection).get(self.month)
        if self.type == "2":
            if self.trimestre:
                name = dict(self._fields['trimestre'].selection).get(self.trimestre) + " Trimestre"
        if self.exercice_id:
            name += " " + self.exercice_id.name
        if self.configuration_id:
            name += "/ " + self.configuration_id.name
        return name

    @api.depends('exercice_id', 'type', 'month', 'trimestre', 'configuration_id')
    def _compute_name(self):
        for record in self:
            record.name = record._get_default_name()

# ====================================== BOUTON ========================================

    def to_draft(self):
        self.state = "draft"
        self.lock_date = False

    def to_lock(self):
        self.state = "lock"
        self.lock_date = datetime.datetime.now()
        self.switch_button = False

    def reinitialisation(self):
        self.write({'switch_button': False})

    def calculate_move(self):
        if self.move_g50_id:
            self.move_g50_id.unlink()

        date_from, date_to  = self._load_date()

        am_cond = "SELECT account_move.id as move_id FROM account_move WHERE "

        if self.company_id.based_on == 'posted_invoices':
            am_cond = am_cond + "(move_type != 'entry' AND state = 'posted' AND date BETWEEN %s AND %s)"

        if self.company_id.based_on == 'payment':
            am_cond = am_cond + "(move_type != 'entry' AND payment_state = 'paid' AND date BETWEEN %s AND %s)"

        query_params = []
        query_params.append(date_from)
        query_params.append(date_to)

        if self.with_move_entry == 'full_move':
            am_cond = am_cond + " OR (move_type = 'entry' AND state = 'posted' AND date BETWEEN %s AND %s)"
            query_params.append(date_from)
            query_params.append(date_to)

        if self.configuration_id.use_invoice_draft:

            if self.company_id.based_on == 'posted_invoices':
                am_cond = am_cond + " OR (move_type != 'entry' AND state = 'draft' AND date BETWEEN %s AND %s)"
                query_params.append(date_from)
                query_params.append(date_to)

            if self.with_move_entry == 'full_move':
                am_cond = am_cond + " OR (move_type = 'entry' AND state = 'draft' AND date BETWEEN %s AND %s)"
                query_params.append(date_from)
                query_params.append(date_to)

        self.env.cr.execute(am_cond, query_params)
        account_moves = self.env.cr.dictfetchall()

        list_move = []
        for i in range(0, len(account_moves)):
            move_id = self.env['account.move'].search([('id','=',account_moves[i]['move_id'])])
            list_move.append((0,0, {
                'move_id':move_id.id,
                'move_line_ids':move_id.line_ids.ids,
                'invoice_line_ids':move_id.invoice_line_ids.ids,
                }))
        
        self.write({'move_g50_id': list_move})

    def calculate_line(self):
        if not self.move_g50_id:
            raise ValidationError(_("Vous devez séléctionner des pièces comptables pour lancer le calcule !"))
        total_ht, total = self._load_invoice_lines()

        line_ids = []
        for line in self.configuration_id.line_tap_ids:
            if line.use_line:
                sub = total
            else:
                sub = 0
            # sub = self._load_accounts(line.definition)
            imposable_ratio = {'C1A11':sub*0.5, 'C1A12':sub*0.7, 'C1A13':sub, 'C1A14':0, 'C1A20': sub }
            sub = abs(sub)
            sub1 = imposable_ratio[line.code] = abs(imposable_ratio[line.code])
            if line.ratio:
                sub1 = sub1 * line.ratio.ratio /100
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'name':line.name,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'imposable': round(imposable_ratio[line.code]),
                 'ratio': line.ratio.id,
                 'total': round(sub1) if sub1 else round(sub)
                 })
            line_ids.append(line_tmp.id)
        self.line_tap_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_ibs_ids:
            if line.use_line:
                sub1 = sub = abs(self._load_accounts(line.definition))
            else:
                sub1 = sub = 0
            if line.ratio:
                sub1 = sub * line.ratio.ratio /100
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'name':line.name,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'ratio': line.ratio.id,
                 'total': round(sub1),
                 })
            line_ids.append(line_tmp.id)
        self.line_ibs_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_irg_ids:
            sub1 = sub = abs(self._load_accounts(line.definition))
            if line.ratio:
                sub1 = sub * line.ratio.ratio /100
            if line.code =="E1L20":
                sub = 0
            if not line.use_line:
                sub1 = sub = 0
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'name': line.name,
                 'ratio': line.ratio.id,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'total': round(sub1) if sub1 else round(sub)
                 })
            line_ids.append(line_tmp.id)
        self.line_irg_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_timbre_ids:
            sub = self._load_accounts(line.definition)
            sub1 = sub = abs(sub)
            if line.ratio:
                sub1 = sub * 100 / line.ratio.ratio
            if not line.use_line:
                sub1 = sub = 0
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'ratio': line.ratio.id,
                 'type_line': line.type_line,
                 'amount': round(sub1),
                 'total': round(sub),
                 })
            line_ids.append(line_tmp.id)
        self.line_timbre_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_autre_ids:
            sub = self._load_accounts(line.definition)
            sub1 = sub = abs(sub)
            if line.ratio:
                sub1 = sub * line.ratio.ratio /100
            if not line.use_line:
                sub1 = sub = 0
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'ratio': line.ratio.id,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'total': round(sub1),
                 })
            line_ids.append(line_tmp.id)
        self.line_autre_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_tva_9_ids:
            if line.use_line:
                sub, exo = self._load_invoice_tva_lines(line.ratio.ratio)
            else:
                sub, exo = [0, 0]
            # sub = self._load_accounts(line.definition)
            sub = abs(sub)
            # exo = abs(self._load_accounts(line.definition_exo))
            sub1 =  sub - exo
            if line.ratio:
                sub1 = sub1 * line.ratio.ratio /100
            line_tmp = self.env['report.g50.line'].create(
               {'code': line.code,
                'name': line.name,
                'ratio': line.ratio.id,
                'type_line': line.type_line,
                'amount': round(sub),
                'amount_exo':  round(exo),
                'imposable': round(sub - exo),
                'total': round(sub1)
                 })
            line_ids.append(line_tmp.id)
        self.line_tva_9_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_tva_19_ids:
            if line.use_line:
                sub, exo = self._load_invoice_tva_lines(line.ratio.ratio)
            else:
                sub, exo = [0, 0]
            # sub = abs(self._load_accounts(line.definition))
            # exo = abs(self._load_accounts(line.definition_exo))
            sub1 =  sub - exo
            if line.ratio:
                sub1 = sub1 * line.ratio.ratio /100
            line_tmp = self.env['report.g50.line'].create(
               {'code': line.code,
                'name': line.name,
                'ratio': line.ratio.id,
                'type_line': line.type_line,
                'amount': round(sub),
                'amount_exo':  round(exo),
                'imposable': round(sub - exo),
                'total': round(sub1)
                 })
            line_ids.append(line_tmp.id)
        self.line_tva_19_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_deduction_ids:
            sub1 = sub = abs(self._load_accounts(line.definition))
            if line.ratio:
                sub1 = sub * line.ratio.ratio /100
            if not line.use_line:
                sub1 = sub = 0
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'name': line.name,
                 'ratio': line.ratio.id,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'total': round(sub1)
                 })
            line_ids.append(line_tmp.id)
        self.line_deduction_ids = [(6, 0, line_ids)]

        line_ids = []
        for line in self.configuration_id.line_tva_p_ids:
            sub1 = sub = abs(self._load_accounts(line.definition))
            if line.ratio:
                sub1 = sub * line.ratio.ratio /100
            if not line.use_line:
                sub1 = sub = 0
            line_tmp = self.env['report.g50.line'].create(
                {'code': line.code,
                 'ratio': line.ratio.id,
                 'type_line': line.type_line,
                 'amount': round(sub),
                 'total': round(sub1)
                 })
            line_ids.append(line_tmp.id)
        self.line_tva_p_ids = [(6, 0, line_ids)]

        self.write({'switch_button': True})

    def recalculate_line(self):   
        self.calculate_line()

# ====================================== FUNCTION ========================================

    def _load_date(self):
        if self.type == '1':
            if not self.month:
                raise ValidationError("Veuillez remplir le mois.")
            int_month = int(self.month)
            int_year = int(self.exercice_id.code)
            var_day = monthrange(int_year, int_month)[1]

            # Premier jour du mois
            var_premier_jour = datetime.date(int_year, int_month, 1)
            # Dernier jour du mois
            var_dernier_jour = datetime.date(int_year, int_month, var_day)

        # Si c'est trimestriel
        if self.type == '2': 
            if not self.trimestre:
                raise ValidationError("Veuillez remplir le trimestre.")
            var_month_end = int(self.trimestre) * 3
            var_month_start = var_month_end - 2
            int_year = int(self.exercice_id.code)
            var_day = monthrange(int_year, var_month_end)[1]

            # Premier jour du trimestre
            var_premier_jour = datetime.date(int_year, var_month_start, 1)
            # Dernier jour du trimestre
            var_dernier_jour = datetime.date(int_year, var_month_end, var_day)
        
        return var_premier_jour, var_dernier_jour

    def _load_move_lines(self):
        move_line_ids = []
        for move in self.move_g50_id:
            for line in move.move_line_ids:
                move_line_ids.append(line.id)
        return move_line_ids

    def _load_invoice_lines(self):
        price_subtotal_invoice_line_sum, price_total_invoice_line_ids_sum = [0, 0]
        for move in self.move_g50_id:
            for line in move.invoice_line_ids:
                price_subtotal_invoice_line_sum += sum(line.mapped('price_subtotal'))
                price_total_invoice_line_ids_sum += sum(line.mapped('price_total'))  
        return price_subtotal_invoice_line_sum, price_total_invoice_line_ids_sum

    def _load_invoice_tva_lines(self, ratio):
        amount_total_wtv, amount_total_wotv = [0, 0]
        for move in self.move_g50_id:
            for line in move.invoice_line_ids:
                amount_total_wtv_line = 0
                for tva in line.tax_ids: 
                    if tva.amount == ratio:
                        amount_total_wtv_line += line.price_total

                if amount_total_wtv_line == 0:
                    for tva in line.product_id.taxes_id:
                        if tva.amount == ratio:
                            amount_total_wtv += line.price_total
                            amount_total_wotv += line.price_total
                amount_total_wtv += amount_total_wtv_line
        return amount_total_wtv, amount_total_wotv

    def _load_line(self, definition):
        definition = ast.literal_eval(definition)

    def _load_accounts(self, definition):
        definition = ast.literal_eval(definition)

        move_line_ids = self._load_move_lines()

        accounts = {}
        if not definition.get('load'):
            return 0
        for x in definition['load']:        # X=+:70:S
            p = x.split(":")                # P=['+', '70', 'S']
            accounts[p[1]] = [p[0], p[2]]   # account={'70': ['+', 'S']}
        _sum = 0.0

        accounts_code = self.env['account.account'].search([]).mapped('code')

        if accounts:
            domain_include = []
            for a in accounts:
                domain_include.append(('code','in',[n for n in accounts_code if str(n).startswith(a)]))
            account_include = self.env['account.account'].search(domain_include)
            move_lines = self.env['account.move.line'].search([('id','in',move_line_ids),('account_id','in', account_include.ids)])

            if accounts[a][1] == 'S':
                _sum_tmp = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))
            if accounts[a][1] == 'D':
                _sum_tmp = sum(move_lines.mapped('debit'))
            if accounts[a][1] == 'C':
                _sum_tmp = - sum(move_lines.mapped('credit'))

            if(accounts[a][0] == '+'):
                _sum += _sum_tmp
            else:
                _sum -= _sum_tmp
        return _sum

# ====================================== RAPPORT ========================================

    def get_dict_value(self):
        total = {}
        tap = {}
        tva = {}
        ratio = {}
        dict_value = {}

        for line in self.line_tap_ids:
            dict_value[line.code] = line.amount
            total[line.code] = line.total
            tap[line.code] = line.imposable

        dict_value['total'] = total
        dict_value['tap'] = tap

        for line in self.line_irg_ids:
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total
            ratio[line.code] = line.ratio.name

        dict_value['ratio'] = ratio

        for line in self.line_ibs_ids:
            if line.definition:
                dict_value['acomptes'] = line.definition
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total

        for line in self.line_timbre_ids:
            dict_value['operations'] = line.definition
            dict_value['timbre_taux'] = line.ratio.name
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total

        for line in self.line_autre_ids:
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total

        for line in self.line_tva_9_ids:
            dict_value[line.code] = line.amount
            tva[line.code] = line.amount_exo
            dict_value['total'][line.code] = line.total
        dict_value['tva'] = tva   

        for line in self.line_tva_19_ids:
            dict_value[line.code] = line.amount
            dict_value['tva'][line.code] = line.amount_exo
            dict_value['total'][line.code] = line.total

        for line in self.line_deduction_ids:
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total

        for line in self.line_tva_p_ids:
            dict_value[line.code] = line.amount
            dict_value['total'][line.code] = line.total

        return dict_value

    def get_trimestre_ara(self, number):
        if number in [1,2,3]:
            return "الأول"
        elif number in [4,5,6]:
            return "الثاني"
        elif number in [7,8,9]:
            return "الثالث"
        else:
            return "الرابع"

    def month_string_to_number_arabic(self, number):
        m = {
            1: 'جانفي',
            2: 'فيفري',
            3: 'مارس',
            4: 'أفريل',
            5: 'ماي',
            6: 'جوان',
            7: 'جويلية',
            8: 'أوت',
            9: 'سبتمبر',
            10: 'أكتوبر',
            11: 'نوفمبر',
            12: 'ديسمبر'
        }
        return m[number]
    
    def action_report(self):
        if not self.date:
            self.date = fields.Date.today()
        if self.configuration_id.type == 'g50':
            return self.env.ref('finnapps_report_g50.report_G50').report_action(self)
        if self.configuration_id.type == 'g50a':
            raise ValidationError("Le rapport sera disponible prochainement")
        if self.configuration_id.type == 'g50ter':
            raise ValidationError("Le rapport sera disponible prochainement")

