from datetime import date
import datetime
from calendar import monthrange
import logging as log
from odoo.exceptions import ValidationError

from odoo import models, fields, api

class FinnDeclarationCotisation(models.Model):
    _name = "finn.declaration.cotisation"
    _description = 'Déclaration des cotisations'

    name = fields.Char('Nom', readonly=True, copy=False, compute="name_cotisation", store=True)

    company_id = fields.Many2one('res.company', string='Société',readonly=True , required=True, index=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Company Currency', readonly=True, related='company_id.currency_id')
    creation_date = fields.Date('Date de création', default = date.today())
    confirm_date = fields.Date('Date de confirmation')
    limit_date = fields.Date('Date limite', compute="_compute_date_limit")
    year = fields.Char('Année', default=str(date.today().year))
    month = fields.Selection(
        [('1', 'Janvier'),
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
        'Mois'
        )

    trimester = fields.Selection(
        [('1', 'Premier trimestre'),
         ('2', 'Deuxième trimestre'),
         ('3', 'Troisième trimestre'),
         ('4', 'Quatrième trimestre')],
        'Trimestre'
        )

    state = fields.Selection(
        [('draft', 'Brouillon'),
         ('calculate', 'Calculé'),
         ('confirme', 'Confirmé'),
         ('cancel', 'Annulé')],
        'État', default="draft")


    line_cotisation_ids = fields.One2many('finn.cotisation.line', 'line_cotisation_id', string='Lignes de cotisation')

    inpu_t =  fields.Integer('Entrée')

    total_effective_in_exercise = fields.Integer('Effective total en exercice')

    output  = fields.Integer('Sortie')

    note  = fields.Text('Note')

    periode = fields.Selection([('1', 'Mensuelle'),('2', 'Trimestrielle')], string="Type de déclaration",)

    total_cotis = fields.Monetary(string='Total', currency_field='currency_id', compute="_compute_cotTot")

    total_patronal = fields.Monetary(string='Total patronal', currency_field='currency_id', compute="_compute_cotpat")

    slip_ids = fields.Many2many('finn.hr.payslip', string='Bulletins de paie')

    journal_id = fields.Many2one('account.journal', string='Journal')
    account_credit_id = fields.Many2one('account.account', string='Compte de crédit')
    account_debit_id = fields.Many2one('account.account', string='Compte de débit')
    move_id = fields.Many2one('account.move', 'Pièce comptable')

    abatement40_id = fields.One2many('finn.abatement.base','abatement40_id', string='Abattement 40%')
    abatement80_id = fields.One2many('finn.abatement.base','abatement80_id', string='Abattement 80%')
    abatement90_id = fields.One2many('finn.abatement.base','abatement90_id', string='Abattement 90%')

    employee_movement_id = fields.One2many('finn.movement.employees','employee_movement_id', string='Mouvement des salariés')

    agency_id = fields.Many2one(
        'res.partner',
        string='Agence',
        domain="[('is_cnas_agency', '=', True)]"
    )

    payment_center_id = fields.Many2one(
        'res.partner', 
        string='Centre de paiement',
        domain="[('parent_id', '=', agency_id),('is_payment_center', '=', True)]"
    )

    lot_declaration_cotisation_id = fields.Many2one('finn.lot.declaration.cotisation', string='Lot de déclaration des cotisations')

    @api.onchange('payment_center_id')
    def onchange_declaration_type(self):
        for record in self:
            record.periode = record.payment_center_id.declaration_type

    @api.onchange('agency_id')
    def onchange_payment_center(self):
        for record in self:
            record.payment_center_id = False

    @api.onchange('payment_center_id')
    def onchange_periode(self):
        for record in self:
            record.trimester = False
            record.month = False

    @api.onchange('month')
    def onchange_trimester(self):
        for record in self:
            if record.month == '3':
                record.trimester = '1'
            elif record.month == '6':
                record.trimester = '2'
            elif record.month == '9':
                record.trimester = '3'
            elif record.month == '12':
                record.trimester = '4'
            else:
                record.trimester = ''

    @api.depends('year','periode','month','trimester')
    def name_cotisation(self): 
        resultat_name = ''       
        for record in self:
            if record.periode == '1':
                month = record._fields['month'].selection
                code_dict = dict(month)
                month = code_dict.get(record.month)
                resultat_name = "%s/%s/%s %s" % (record.agency_id.name,record.payment_center_id.name, month, record.year)
            elif record.periode == '2':
                trimester = record._fields['trimester'].selection
                code_dict = dict(trimester)
                trimester = code_dict.get(record.trimester)
                resultat_name = "%s/%s/%s %s" % (record.agency_id.name, record.payment_center_id.name, trimester, record.year)
            record.name = resultat_name

    _sql_constraints = [
        ('cnas_name_uniq', 'UNIQUE (agency_id.name, payment_center_id.name, month, trimester, year)', "Vous ne pouvez pas créer deux déclaration dans la même période pour le même centre de paiement."),
    ]

    # Calcule des entrées
    def input_employees(self, employee, var_premier_jour, var_dernier_jour):
        if employee.contract_id.date_start >= var_premier_jour and employee.contract_id.date_start <= var_dernier_jour:
            return employee

    # Calcule des sorties
    def output_employees(self, employee, var_premier_jour, var_dernier_jour):
        if employee.contract_id.date_end != False and employee.contract_id.date_end >= var_premier_jour and employee.contract_id.date_end <= var_dernier_jour:
            return employee

    # Calcule de l'effectif
    def total_employees(self, employee, var_premier_jour, var_dernier_jour):
        
        for rule in employee.contract_id.struct_id.rule_ids:
            if rule.code == 'SS':
                if employee.contract_id.date_start <= var_dernier_jour:
                    if  employee.contract_id.date_end:
                        if employee.contract_id.date_end >= var_premier_jour:
                            return employee
                    if  employee.contract_id.date_end == False :
                        return employee

    #get employee mov per cnas agency
    def company_empl_agencies(self):

        employee = self.employee_movement_id.mapped(lambda emp: emp.employee_id)
        company_agencies = employee.mapped(lambda emp: emp.agency_id)
                
        data = {
            'employee': employee,
            'company_agencies': company_agencies,
        }
        return data
        
    def calculer_lignes_cotisation(self):
        # Vider le tableau des lignes de cotisations et initialisation
        self.line_cotisation_ids.unlink()
        self.abatement40_id.unlink()
        self.abatement80_id.unlink()
        self.abatement90_id.unlink()
        self.employee_movement_id.unlink()
        rec_input = []
        rec_output = []
        rec_total = []
        self.total_effective_in_exercise = 0
        var_premier_jour = datetime.date(2022, 1, 1)
        var_dernier_jour = datetime.date(2022, 12, 31)

        # == Mensuel ou trimetriel ==
        # Si c'est mensuel
        if self.periode == '1':
            if not self.month:
                raise ValidationError("Veuillez remplir le mois.")
            int_month = int(self.month)
            int_year = int(self.year)
            var_day = monthrange(int_year, int_month)[1]

            # Premier jour du mois
            var_premier_jour = datetime.date(int_year, int_month, 1)
            # Dernier jour du mois
            var_dernier_jour = datetime.date(int_year, int_month, var_day)

        # Si c'est trimestriel
        if self.periode == '2':
            if not self.month:
                raise ValidationError("Veuillez remplir le trimestre.")
            var_month_end = int(self.trimester) * 3
            var_month_start = var_month_end - 2
            int_year = int(self.year)
            var_day = monthrange(int_year, var_month_end)[1]

            # Premier jour du trimestre
            var_premier_jour = datetime.date(int_year, var_month_start, 1)
            # Dernier jour du trimestre
            var_dernier_jour = datetime.date(int_year, var_month_end, var_day)

        # Récupérer les employés avec un contrat en cours
        contracts = self.env['hr.contract'].search([('struct_id.code','in', ['STCH','STCJ'])])
        employees = self.env['hr.employee'].search([
            ('contract_id','!=', False),
            ('contract_id','not in', contracts.ids),
            ('payment_center_id','=', self.payment_center_id.id)
        ])

        for employee in employees:
            # Calcule des entrées
            result = self.input_employees(employee, var_premier_jour, var_dernier_jour)
            if result :
                rec_input.append(result)
            # Calcule des sorties
            result = self.output_employees(employee, var_premier_jour, var_dernier_jour)
            if result:
                rec_output.append(result)
            # Calcule de l'effectif
            result = self.total_employees(employee, var_premier_jour, var_dernier_jour)
            if result:
                rec_total.append(result)

        self.inpu_t = len(rec_input)    
        self.output = len(rec_output)
        self.total_effective_in_exercise = len(rec_total)

        # Calcule des lignes de cotisation
        some_cot_r22, some_cot_r06, some_cot_r07, some_cot_r08 = (0,0,0,0)

        sublines = self.env['finn.hr.payslip.line'].search([
            ('category_id.code', 'in', ['BASIC','COT']),
            ('slip_id.date_from','>=',var_premier_jour),
            ('slip_id.date_to','<=',var_dernier_jour),
            ('employee_id.payment_center_id','=', self.payment_center_id.id),])

        for subline in sublines:
            # Vérifier si la structure du bulletin de paie de la ligne à une SS
            for rule in subline.slip_id.struct_id.rule_ids:
                if rule.code == 'SS':
                    if subline.employee_id.nat_cot1 == 'R22':
                        some_cot_r22 += subline.total
                    if subline.employee_id.nat_cot1 == 'R06':
                        some_cot_r06 += subline.total
                    if subline.employee_id.nat_cot1 == 'R07':
                        some_cot_r07 += subline.total
                    if subline.employee_id.nat_cot1 == 'R08':
                        some_cot_r08 += subline.total

        some_cot_r98 = some_cot_r22 + some_cot_r06 + some_cot_r07 + some_cot_r08        

        # Création des lignes de cotisation
        cot_vals = []

        cot_vals.append((0,0,{
            'code': 'R22',
            'nature_cotisation': 'RÉGIME GÉNÉRAL',
            'assiette': some_cot_r22,
            'taux': 34.5,
            'company_id':self.company_id.id,
        }))

        cot_vals.append((0,0,{
            'code': 'R06',
            'nature_cotisation': 'BÉNÉFICIAIRES ABATTEMENT 40%',
            'assiette': some_cot_r06,
            'taux': 24.5,
            'company_id':self.company_id.id,
        }))

        cot_vals.append((0,0,{
            'code': 'R07',
            'nature_cotisation': 'BÉNÉFICIAIRES ABATTEMENT 80%',
            'assiette': some_cot_r07,
            'taux': 14.5,
            'company_id':self.company_id.id,
        }))

        cot_vals.append((0,0,{
            'code': 'R08',
            'nature_cotisation': 'BÉNÉFICIAIRES ABATTEMENT 90%',
            'assiette': some_cot_r08,
            'taux': 19.5,
            'company_id':self.company_id.id,
        }))

        cot_vals.append((0,0,{
            'code': 'R98',
            'nature_cotisation': 'FNPOS RÉGIME GÉNÉRAL',
            'assiette': some_cot_r98,
            'taux': 0.50,
            'company_id':self.company_id.id,
        }))

        self.write({'line_cotisation_ids': cot_vals})
        
        #calcule lignes abatement40_id
        stage_cons = self.env['hr.payroll.structure.type'].search([('name','in', ['Consultant','Stagiaire'])])
        abatement40 = []
        emplye_06 = self.env['hr.employee'].search([            
            ('contract_id.structure_type_id','not in',stage_cons.ids),
            ('slip_ids.date_from','>=',var_premier_jour),
            ('slip_ids.date_to','<=',var_dernier_jour),
            ('nat_cot1','in', ['R06']),
            ('payment_center_id','=', self.payment_center_id.id),
        ])
        if len(emplye_06) != 0:
            for emp_06 in emplye_06:
                some_cot_emp = 0
                emp_lines = self.env['finn.hr.payslip.line'].search([
                    ('employee_id.id', '=', emp_06.id),
                    ('category_id.code', 'in', ['BASIC','COT']),
                    ('slip_id.date_from','>=',var_premier_jour),
                    ('slip_id.date_to','<=',var_dernier_jour)])
                for line in emp_lines:
                    some_cot_emp += line.total
                abatement40.append((0,0,{
                    'employee_id': emp_06.id,
                    'base': some_cot_emp,
                    }))

            self.write({'abatement40_id': abatement40})
        #===========================================
        #calcule lignes abatement80_id
        abatement80 = []
        emplye_07 = self.env['hr.employee'].search([
            ('contract_id.structure_type_id','not in',stage_cons.ids),
            ('slip_ids.date_from','>=',var_premier_jour),
            ('slip_ids.date_to','<=',var_dernier_jour),
            ('nat_cot1','in', ['R07']),
            ('payment_center_id','=', self.payment_center_id.id),    
        ])
        if len(emplye_07) != 0:
            for emp_07 in emplye_07:
                some_cot_emp = 0
                emp_lines = self.env['finn.hr.payslip.line'].search([
                    ('employee_id.id', '=', emp_07.id),
                    ('category_id.code', 'in', ['BASIC','COT']),
                    ('slip_id.date_from','>=',var_premier_jour),
                    ('slip_id.date_to','<=',var_dernier_jour)])
                for line in emp_lines:
                    some_cot_emp += line.total
                abatement80.append((0,0,{
                    'employee_id': emp_07.id,
                    'base': some_cot_emp,
                    }))

            self.write({'abatement80_id': abatement80})
        #================================================
        #calcule lignes abatement90_id
        abatement90 = []
        emplye_08 = self.env['hr.employee'].search([
            ('contract_id.structure_type_id','not in',stage_cons.ids),
            ('slip_ids.date_from','>=',var_premier_jour),
            ('slip_ids.date_to','<=',var_dernier_jour),
            ('nat_cot1','in', ['R08']),
            ('payment_center_id','=', self.payment_center_id.id),    
        ])
        if len(emplye_08) != 0:
            for emp_08 in emplye_08:
                some_cot_emp = 0
                emp_lines = self.env['finn.hr.payslip.line'].search([
                    ('employee_id.id', '=', emp_08.id),
                    ('category_id.code', 'in', ['BASIC','COT']),
                    ('slip_id.date_from','>=',var_premier_jour),
                    ('slip_id.date_to','<=',var_dernier_jour)])
                for line in emp_lines:
                    some_cot_emp += line.total
                abatement90.append((0,0,{
                    'employee_id': emp_08.id,
                    'base': some_cot_emp,
                    }))

            self.write({'abatement90_id': abatement90})
        
        #===========================================================
        #calcule lignes employee_movement_id entré
        input_employe_mov = []
        for emp_input in rec_input:
            input_employe_mov.append((0,0,{
                'employee_id': emp_input.id,
                'output_input': 'E',
                'date_out_input': emp_input.contract_id.date_start,
                'observation': 'Recrutement',
                'employee_agency': emp_input.agency_id.name,
            }))

        self.write({'employee_movement_id': input_employe_mov})
        #===========================================================
        #calcule lignes employee_movement_id sortie
        out_employe_mov = []
        for emp_out in rec_output:
            out_employe_mov.append((0,0,{
                'employee_id': emp_out.id,
                'output_input': 'S',
                'date_out_input': emp_out.contract_id.date_end,
                'observation': emp_out.contract_id.motif1.name,
                'employee_agency': emp_out.agency_id.name,
            }))
        self.write({'employee_movement_id': out_employe_mov})

    @api.depends('creation_date')
    def _compute_date_limit(self):
        for record in self:
            record.limit_date = record.creation_date + datetime.timedelta(days=30)

    @api.depends('line_cotisation_ids')
    def _compute_cotTot(self):
        self.total_cotis = 0
        for record in self:
            if record.line_cotisation_ids:
                for coti in record.line_cotisation_ids:
                    record.total_cotis += coti.assiette * coti.taux / 100

    @api.depends('line_cotisation_ids')
    def _compute_cotpat(self):
        for record in self:
            if record.line_cotisation_ids:
                for coti in record.line_cotisation_ids:
                    if coti.code != 'R98':
                        record.total_patronal += coti.assiette * (coti.taux - 9) / 100
                    if coti.code == 'R98':
                        record.total_patronal += coti.assiette * coti.taux / 100
                return
            record.total_patronal = 0

    def calculate(self):
        if self.periode == '1':
            if self.month == "":
                raise models.ValidationError("Veuillez remplir le mois")
        if self.periode == '2':
            if self.trimester == "":
                raise models.ValidationError("Veuillez remplir le trimsetre")
        self.calculer_lignes_cotisation()
        self.state = ('calculate')

    def realculate(self):
        if self.periode == '1':
            if self.month == "":
                raise models.ValidationError("Veuillez remplir le mois")
        if self.periode == '2':
            if self.trimester == "":
                raise models.ValidationError("Veuillez remplir le trimsetre")
        self.calculer_lignes_cotisation()

    def confirm(self):
        if self.journal_id and self.account_debit_id and self.account_credit_id:
            # Préparation des valeurs de la pièce comptable
            move_vals = {
                    'ref': self.name,
                    'journal_id': self.journal_id.id,
                    'date': date.today(),
                    }

            # Création d'un pièce comptable
            move = self.env['account.move'].create(move_vals)

            # Préparation des écritures comptable
            move_lines_vals = ({
                    'name': self.name,
                    'debit': self.total_patronal,
                    'account_id': self.account_debit_id.id,
                    'move_id': move.id,
                    },
                    {
                    'name': self.name,
                    'credit': self.total_patronal,
                    'account_id': self.account_credit_id.id,
                    'move_id': move.id,
                    })

            move_lines = self.env['account.move.line'].with_context(check_move_validity=False).create(move_lines_vals)

            self.move_id = move.id

            # fonction de lettrage
            # self._partial_reconcile(inv, debit_moves, credit_moves)

            # Validation de la pièce comptable
            move.action_post()
            self.confirm_date = date.today()
            self.state = ('confirme')
        else:
            raise ValidationError("Veuillez remplir les informations comptables.")


    def cancel(self):
        self.move_id.button_draft()
        self.move_id.unlink()
        self.state = ('cancel')

    def drafter(self):
        self.state = ('draft')

    def print_repport(self):
        return self.env.ref('finnapps_hr_cnas_reports.declaration_cotisation_repport').report_action(self)

    def unlink(self):
        for rec in self:
            if rec.state == "confirme":
                raise ValidationError("Vous ne pouvez pas supprimer une déclaration confirmé.")
        res = super(FinnDeclarationCotisation, self).unlink()
        return res
