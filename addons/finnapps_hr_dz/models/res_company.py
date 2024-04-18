# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging as log

class ResCompany(models.Model):

    _inherit = 'res.company'

    forme_juridique = fields.Many2one(
        'finn.forme.juridique', 
        string='Forme juridique',
        )

    @api.model
    def _init_data_resource_calendar(self):
        log.warning('heree')
        
    def _create_resource_calendar(self):
        log.warning('')