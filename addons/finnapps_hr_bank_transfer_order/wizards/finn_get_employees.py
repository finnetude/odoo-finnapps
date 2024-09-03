from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging as log



class FinnGetEmployees(models.TransientModel):

    _name = 'finn.get.employees'
    _description= "Récupérer les employés"


    



    transfer_order_id = fields.Many2one('finn.transfer.order',string="Ordre de virement")
    date_from = fields.Date(string="De", required=True)
    date_to = fields.Date(string="À", required=True)


    hr_bank_ids = fields.Many2many(
        'res.bank',
        string="Banques",
        )


    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employés",
        compute="compute_employee_ids" 
        )
    

    label_line = fields.Char(
        string="Générer la libellé de la ligne", 
        compute="compute_label_line"
        )

    @api.depends('transfer_order_id')
    def compute_label_line(self):
        letter_month = ''
        year = ''
        for record in self:
            
            number_month = record.transfer_order_id.transfer_order_date.month
            year = record.transfer_order_id.transfer_order_date.year
            if number_month == 1:
                letter_month = 'Janvier'
            if number_month == 2:
                letter_month = 'Février'
            if number_month == 3:
                letter_month = 'Mars'
            if number_month == 4:
                letter_month = 'Avril'
            if number_month == 5:
                letter_month = 'Mai'
            if number_month == 6:
                letter_month = 'Juin'
            if number_month == 7:
                letter_month = 'Juillet'
            if number_month == 8:
                letter_month = 'Août'
            if number_month == 9:
                letter_month = 'Septembre'
            if number_month == 10:
                letter_month = 'Octobre'
            if number_month == 11:
                letter_month = 'Novembre'
            if number_month == 12:
                letter_month = 'Décembre'
        if letter_month:
            record.label_line = letter_month.upper() + ' ' + str(year)
        else:
            record.label_line = ''
    

    @api.depends('date_from','date_to','hr_bank_ids')
    def compute_employee_ids(self):
        for record in self:
            employees = []
            payslips = self.env['finn.hr.payslip'].search(
                    [('date_to','=',record.date_to),
                    ('date_from','=',record.date_from),
                    ('contract_id.payement_mode.name','!=','Espèce'),
                    ('contract_id.employee_id.bank_account_id.bank_id.id','in', record.hr_bank_ids.ids)
                    ]).mapped('employee_id')

            if payslips and record.date_from and record.date_to:
                
                record.employee_ids = [(6, 0, payslips.ids)]
            else:
                record.employee_ids = False
                



    def validate_getting(self):
        if not self.date_from or not self.date_to:
            raise models.ValidationError("Veuillez remplir les dates")
        for record in self:
            record.transfer_order_id.transfer_order_line_ids = False
            targeded_payslips = self.env['finn.hr.payslip'].search([
                ('date_to','>',record.date_from),
                ('date_from','<',record.date_to),
                ('employee_id','in', record.employee_ids.ids)])

            for payslip in targeded_payslips:
                net = 0.0
                transfer_order_line_one = record.env['finn.transfer.order.line']
                for line in payslip.line_ids:
                    if line.code == "NET":
                        net = line.total
                
                vlues = {
                    'transfer_order_id': record.transfer_order_id.id,
                    'beneficiary_id':payslip.employee_id.bank_account_id.partner_id.id if payslip.employee_id.bank_account_id.partner_id.id else False,
                    'bank_account_id': payslip.employee_id.bank_account_id.id if payslip.employee_id.bank_account_id.id else False,
                    'operation_amount': net,
                    'label': "Paie " + record.label_line,
                    }
                transfer_order_line_one.create(vlues)
                record.transfer_order_id.bank_ids = [(6, 0, record.hr_bank_ids.ids)]


