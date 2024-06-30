# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging as log


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=False, readonly=True, compute='_amount_all_v2', tracking=True)
    # tax_totals_tva = fields.Binary(compute='_compute_tax_totals_v2', exportable=False)
    tax_totals = fields.Binary(compute='_compute_tax_totals_v2', exportable=False)
    amount_tax = fields.Monetary(string='Taxes', store=False, readonly=True, compute='_amount_all_v2')
    amount_tax_tva = fields.Monetary(string='Taxes 1%', store=False, readonly=True, compute='_amount_all_v2')
    amount_total_tva = fields.Monetary(string='Total', store=False, readonly=True, compute='_amount_all_v2')
    amount_total = fields.Monetary(string='Total', store=False, readonly=True, compute='_amount_all_v2')

    @api.depends_context('lang')
    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_v2(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            total = self.env['account.tax']._prepare_tax_totals(
                [x._convert_to_tax_base_line_dict() for x in order_lines],
                order.currency_id or order.company_id.currency_id,
            ) 
            # order.tax_totals_tva = total
            order.tax_totals = total

    @api.depends('order_line.price_total')
    def _amount_all_v2(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax 
            order.amount_total_tva = order.amount_untaxed + order.amount_tax
            order.amount_tax_tva = order.amount_total_tva * 0.01
            order.amount_total = order.amount_total_tva + order.amount_tax_tva
        
