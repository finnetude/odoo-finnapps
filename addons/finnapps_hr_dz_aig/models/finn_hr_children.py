# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

import logging as log

# Mode de paiement
class FinnHrChildren(models.Model):
    _name = 'finn.hr.children'
    name = fields.Char(string='Prenom')
    parent_id = fields.Many2one('hr.employee',string='Parent')