# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging as log

class employee(models.Model):

    _inherit = 'hr.employee'

    childrens_ids = fields.One2many('finn.hr.children','parent_id',string='Childrens')

