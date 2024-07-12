from odoo import models, fields, api, _
import logging
class HrPayslip(models.Model):
    

    _inherit = 'finn.hr.payslip'


    hr_payment_state = fields.Selection(
        string="État de paiement",
        selection=[
            ('unpaid','Non payé'),
            ('partially_paid','Payé partiellement'),
            ('paid','Payé')],
        copy=False)
    

    currency_id = fields.Many2one(
        'res.currency',
        related="company_id.currency_id"
    )
    

    payments_ids = fields.Many2many(
        'account.move',
        string="Paiements",
        readonly=True,
        copy=False
        )

    payment_date = fields.Date(
        string="Payé le",
        copy=False
        )

    still_to_pay = fields.Monetary(
        string="Reste à payé",
        compute="compute_still_to_pay"
        )

    net_amount = fields.Monetary(
        string="Net",
        compute="compute_net_amount"
        )

    
    @api.depends('line_ids')
    def compute_net_amount(self):
        for record in self:
            record.net_amount = 0.0
            for line in record.line_ids:
                if line.code == "NET":
                    record.net_amount = abs(line.total)


    def compute_still_to_pay(self):
        for record in self:
            record.still_to_pay = 0.0
            total_payment = 0.0
            for l in record.payments_ids:
                total_payment += l.amount_total_signed

            record.still_to_pay = abs(record.net_amount - total_payment)




    def hr_payment_register(self):
        return {
            'name': 'Enregistrer un paiement de bulletin de paie',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': 'hr_payslip_payment_register',
            'res_model': 'hr.payslip.payment.register',
            'context': {
                'default_payslip_id':self.id, 
                'default_payment_type': 'payslip',
                'default_amount': self.still_to_pay,
                'default_amount_to_pay':self.still_to_pay,
                },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # Annuler le lettrage et supprimer la pièce compatable
    def action_payslip_cancel(self):
        self.move_id.line_ids.remove_move_reconcile()
        for line in self.payments_ids:
            line.button_draft()
            line.button_cancel()
            line.posted_before = False
            line.unlink()
        self.payment_date = False
        self.hr_payment_state = 'unpaid'
        
        res = super(HrPayslip, self).action_payslip_cancel()
        return res
