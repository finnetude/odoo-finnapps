# -*- encoding: utf-8 -*-group
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

class AccountGroup(models.Model):
    _inherit = 'account.group'

    @api.depends('account_ids', 'account_ids.debit', 'account_ids.credit', 'account_ids.balance',
                 'group_ids', 'group_ids.debit', 'group_ids.credit', 'account_ids.balance')
    def _compute_debit_credit(self):
        for record in self:
            record.debit = sum(record.account_ids.mapped('debit')) + sum(record.group_ids.mapped('debit'))
            record.credit = sum(record.account_ids.mapped('credit')) + sum(record.group_ids.mapped('credit'))
            record.balance = sum(record.account_ids.mapped('balance')) + sum(record.group_ids.mapped('balance'))

    def parent_groups(self):
        groups_ids = [self.id] + self.group_ids.ids
        for child_group_id in self.group_ids:
            if child_group_id:
                groups_ids += child_group_id.parent_groups()
        return groups_ids
        
    debit = fields.Float(
        string="Debit",
        compute='_compute_debit_credit',
        store=True,
        recursive=True,
    )

    credit = fields.Float(
        string="Credit",
        compute='_compute_debit_credit',
        store=True,
        recursive=True,
    )

    balance = fields.Float(
        string="Balance",
        compute='_compute_debit_credit',
        store=True,
    )

    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='group_id',
        string='Comptes liés'
    )

    group_ids = fields.One2many(
        comodel_name='account.group',
        inverse_name='parent_id',
        string='Groupes liés'
    )
