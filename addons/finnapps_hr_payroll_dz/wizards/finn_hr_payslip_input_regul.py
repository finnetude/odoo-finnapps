from odoo import api, fields, models, _

import logging as log

class FinnHrPayslipInputRegul(models.TransientModel):
    """populates payroll social security data for the ats"""

    _name = 'finn.hr.payslip.input.regul'
    _description = 'Régulations'


    payslip_id  = fields.Many2one('finn.hr.payslip', string="Bulletin de paie")
    rule_id     = fields.Many2one('finn.hr.salary.rule', string="Régulation", domain="[('id_regul_rule','=',True)]")
    code        = fields.Char(string="Code", related='rule_id.code')
    amount      = fields.Float(string="Montant")

    def add_regul_input(self):
        input = self.payslip_id.input_line_ids.search([('payslip_id','=',self.payslip_id.id),('code','=',self.rule_id.code)], limit=1)

        if input:
            input.amount = self.amount
        else:
            self.payslip_id.input_line_ids.create({
                'name': self.rule_id.name,
                'code': self.rule_id.code,
                'contract_id': self.payslip_id.contract_id.id,
                'payslip_id': self.payslip_id.id,
                'amount': self.amount,
                })
