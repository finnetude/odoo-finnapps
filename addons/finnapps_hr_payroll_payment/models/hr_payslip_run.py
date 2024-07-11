from odoo import models, fields, api, _

class HrPayslipRun(models.Model):
    

    _inherit = 'finn.hr.payslip.run'


    hr_run_payment_state = fields.Selection(
        string="État de paiement",
        selection=[
            ('unpaid','Non payé'),
            ('paid','Payé'),
            ])

   


    total_net = fields.Float(
        string="Total Net",
        compute="compute_total_net"
    )


    @api.depends('slip_ids')
    def compute_total_net(self):
        self.total_net = 0.0
        for record in self:
            for slip in record.slip_ids:
                for line in slip.line_ids:
                    if line.code == "NET":
                        record.total_net += line.total 


    @api.onchange('slip_ids.state')
    def onchange_hr_run_payment_state(self):
        for record in self:
            for slip in record.slip_ids:
                if slip.hr_payment_state == 'paid':
                    record.hr_run_payment_state = 'paid'
                elif slip.hr_payment_state == 'unpaid':
                    record.hr_run_payment_state = 'unpaid'



    def hr_payment_run_register(self):
        return {
            'name': 'Enregistrer un paiement de lot des bulletins de paie',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': 'hr_payslip_payment_register',
            'res_model': 'hr.payslip.payment.register',
            'context': {
                'default_payslip_run_id':self.id, 
                'default_payment_type': 'payslip_run',
                'default_amount': self.total_net,
                },
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

