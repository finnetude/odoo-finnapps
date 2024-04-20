# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging as log

class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.depends('move_line_ids', 'move_line_ids.debit', 'move_line_ids.credit')
    def _compute_debit_credit(self):
        for record in self:
            record.debit = sum(record.move_line_ids.mapped('debit'))
            record.credit = sum(record.move_line_ids.mapped('credit'))
            record.balance = record.debit - record.credit

    debit = fields.Monetary(
        string="Debit",
        compute='_compute_debit_credit',
        store=True,
    )

    credit = fields.Monetary(
        string="Credit",
        compute='_compute_debit_credit',
        store=True,
    )

    balance = fields.Monetary(
        string="Balance",
        compute='_compute_debit_credit',
        store=True,
    )

    move_line_ids = fields.One2many(
        string='ecritures comptable',
        comodel_name='account.move.line',
        inverse_name='account_id',
    )

