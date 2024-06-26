# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging as log

class employee(models.Model):

    _inherit = 'hr.employee'

    birth_act = fields.Char(string='N° de l’acte de naissance')
    childrens_ids = fields.One2many('finn.hr.children','parent_id',string='Childrens')

