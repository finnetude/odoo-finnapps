# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging as log

class ResCompany(models.Model):

    _inherit = 'res.company'

    employer_number = fields.Char("N°: Employeur")