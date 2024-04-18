from odoo import models, fields, api, _
from datetime import date
import logging as log

global_datas = {}

class FinnHrAttestationTravailSalaire(models.Model):
    """ ATS model for defining an ats object in order 
        to declare working days and salary """

    _name = 'finn.hr.ats'
    _description = 'Attestation de travail et de salaire'

    name = fields.Char(string="Nom")

    employee_id         = fields.Many2one('hr.employee', string="Employé(e)", domain="[('contract_ids', '!=', False)]", required=True)
    company_id          = fields.Many2one('res.company' , string = 'Société' ,default=lambda self: self.env.company)
    ats_wiz_ids         = fields.One2many('finn.hr.ats.line', 'ats_wiz_id', compute='_get_ats_line',)
    agency_id           = fields.Many2one('res.partner', string='Agence', domain="[('is_cnas_agency', '=', True)]")
    payment_center_id   = fields.Many2one('res.partner', string='Centre de paiement', domain="[('parent_id', '=', agency_id),('is_payment_center', '=', True)]")

    date_dernier    = fields.Date("Date du dernier jour de travail",)
    date_reprise    = fields.Date("Date de reprise",)
    date_start      = fields.Date(string="De",)
    date_end        = fields.Date(string="Au", default=fields.Date.today,)
    date_jour       = fields.Date()

    name_report     = fields.Selection([('recto', 'ATS Recto'),('verso', 'ATS Verso')], default="recto",  string="Nom de rapport")
    duration_int    = fields.Selection( [('inf', 'Inferieur à 6 mois/maternité'),('sup', 'Superieur à 6 mois/invalidité')], string="En cas d'arrêt de travail",)

    duration_trav   = fields.Integer(string="Periode de travail en jour(s)", default=90,)
    hours           = fields.Integer(string="durée heurs",)

    is_demission    = fields.Boolean(string="Est une démission?",)
    work_stop       = fields.Boolean(string="L'interessé(e) n'a pas repris son travail à ce jour",)

    @api.constrains('employee_id')
    def get_default_start(self):
        """ calculates start date of the ats based on contract date """
        for record in self:
            now = date.today().year
            now_date = date(now, 1, 1)
            if record.employee_id.contract_id.date_start :
                date_start = record.employee_id.contract_id.date_start
                duration = (now_date - date_start).days + 1
                if duration > 0:
                    record.date_start = now_date
                else:
                    record.date_start = date_start

    @api.depends('employee_id', 'date_start','date_end')
    def name_get(self):
        result = []
        for record in self:
            name = record.employee_id.name + ' ' + ' (' + str(record.date_start)+ '/' + str(record.date_end)+ ' )' 
            result.append((record.id, name))
        return result

    @api.model
    def get_datas(self):
        global global_datas
        return global_datas

   

    # Vérification si la date de début de l'ATS correspond à date de début du contrat
    @api.constrains('date_start')
    def onchange_date_start(self):
        for record in self:
            contrat = self.env['hr.contract'].search([('employee_id','=',record.employee_id.id)])
            contrat_date_start = None
            for ctr in contrat:
                if ctr.state == 'open':
                    contrat_date_start = ctr.date_start
            if record.date_start < contrat_date_start:
                raise Warning(_('%s') % "La date selectionne doit être posterieur à la date de début du contrat")

    @api.onchange('work_stop')
    def onchange_work_stop(self):
        """ This function change the value of date_jour
            to system date when work_stop is True 
        """
        self.is_demission = False
        if self.work_stop:
            self.date_jour = date.today()
        else:
            self.date_jour = False

    @api.onchange('employee_id')
    def onchange_agency(self):
        if self.employee_id:
            self.agency_id = self.employee_id.agency_id.id
            self.payment_center_id = self.employee_id.payment_center_id.id
        else:
            self.agency_id = False
            self.payment_center_id = False



    @api.depends('date_start','date_end')
    def _get_ats_line(self):
        """get all ats payroll lines"""
        for record in self:
            payslip_obj = self.env['finn.hr.payslip']
            lines = []
            payslip_ids = payslip_obj.search([
                ('date_from', '>=', record.date_start),
                ('date_to', '<=', record.date_end),
                ('contract_id', '=',record.employee_id.contract_id.id),
                ('credit_note', '=', False),
                ('refund_payslip', '=', False)
            ])
            
            for payslip_id in payslip_ids:
                line_work = self.env['finn.hr.payslip.worked_days'].search([
                    ('payslip_id', '=', payslip_id.id),
                    ('code', '=', 'WORK100')
                ])
                line_conge = self.env['finn.hr.payslip.worked_days'].search([
                    ('payslip_id', '=', payslip_id.id),
                    ('code', '=', 'CP')
                ])

                month = payslip_id.date_from.strftime('%B')
                year = payslip_id.date_from.strftime('%Y')
                mois = ''

                dict_month = {
                    'January':'janvier',
                    'February':'Février',
                    'March':'Mars',
                    'April':'Avril',
                    'May':'Mai',
                    'June':'Juin',
                    'July':'juillet',
                    'August':'Août',
                    'September':'Septembre',
                    'October':'Octobre',
                    'November':'Novembre',
                    'December':'Décembre'}

                mois = dict_month[month]

                line_salary = self.env['finn.hr.payslip.line'].search(
                    [('slip_id', '=', payslip_id.id),
                     ('code', '=', 'SS')])

                created = self.env['finn.hr.ats.line'].create({
                    'worked_days':line_work.number_of_days + line_conge.number_of_days,
                    'month_year': "%s %s" % (mois, year),
                    'cotisation': round(line_salary.amount, 2),
                    'cotisation_amount': round(line_salary.total, 2)
                })
                lines.append(created.id)

            record.ats_wiz_ids = [(6, 0, lines)]

class FinnHrAttestationTravailSalaire(models.Model):
    """Lines populated from the payroll"""
    _name = 'finn.hr.ats.line'
    _description = 'Ligne d\'attestation de travail et de salaire'

    ats_wiz_id = fields.Many2one(
        'finn.hr.ats',
    )
    
    month_year = fields.Char(
        string="Mois et année",
    )

    worked_days = fields.Float(
        string="Nombre de jour travaillés",
    )
    
    cotisation = fields.Float(
        string="Cotisation",
    )
    
    cotisation_amount = fields.Float(
        string="Cotisation",)
    
    motif = fields.Char(
        string="Motif des absences",
    )

