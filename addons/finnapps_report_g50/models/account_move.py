
from datetime import date
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('payment_state')
    def compute_paid_date(self):
        for record in self:
            if record.payment_state ==  'paid':
                record.paid_date = date.today()
            else :
                record.paid_date = False
            
    paid_date = fields.Date('Date de paiement',compute='compute_paid_date', store=True)
