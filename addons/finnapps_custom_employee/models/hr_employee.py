# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging as log

class employee(models.Model):

    _inherit = 'hr.employee'
    
    registration_number = fields.Char(string="Matricule",default="")
    _sql_constraints = [
        ('unique_registration_number', 'UNIQUE (registration_number)', "The Registration Number already exists"),
    ]
