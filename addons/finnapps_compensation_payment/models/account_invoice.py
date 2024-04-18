from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging as log

class AccountInvoiceInherited(models.Model):
    _inherit = 'account.move'

    # Fonction pour l'affichage du bouton <Paiement par compensation>
    @api.depends('state')
    def _calc_show_compensation(self):
        for rec in self:
            rec.show_compensation_button = False
            if rec.state in ('posted') and rec.move_type == 'out_invoice' and rec.payment_state != 'paid':
                rec.show_compensation_button = True

    show_compensation_button = fields.Boolean(
        default=False,
        compute='_calc_show_compensation',
        help="Booléen pour l'affichage du bouton <Paiement par compensation>"
        )

    compensation_invoice_id = fields.Many2one(
        'account.move'
        )

    compensation_invoice_ids = fields.One2many(
        'account.move',
        'compensation_invoice_id'
        )

    total_compensation = fields.Monetary(
        default=0.0,
        copy=False
        )
    
    
    

    
    #
    def action_view_compensation_invoices(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]

        if len(self.compensation_invoice_ids) > 1:
            action['domain'] = [('id', 'in', self.compensation_invoice_ids.ids)]
        
        elif len(self.compensation_invoice_ids) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = self.compensation_invoice_ids.id
        
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action