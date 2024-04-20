# -*- coding: utf-8 -*-

from . import models
from odoo import api, SUPERUSER_ID, _

import logging

def generate_hierarchy_account(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    for account_id in env['account.account'].search([]):
        curr_group_id = account_id.group_id
        if curr_group_id:
            group_ids = curr_group_id

            while curr_group_id.code_prefix_start != '0':
                curr_group_id = curr_group_id.parent_id
                group_ids += curr_group_id

            account_id.update({'hierarchy_group_ids' : [(6, 0, group_ids.ids)]})
