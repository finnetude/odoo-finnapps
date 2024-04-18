# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    commune_id = fields.Many2one(
        "finn.res.country.state.commune",
        'Commune',
        domain="[('state_id','=',state_id)]"
    )

    localite_id = fields.Many2one(
        "finn.res.country.state.localite",
        'Localité',
        domain="[('state_id','=',state_id)]"
    )

    @api.onchange('state_id')
    def _onchange_state(self):
        pass

    #set state_id to False if another country get selected
    @api.onchange('country_id')
    def empty_state(self):
        for record in self:
            record.state_id = False

    #set commune_id to False if another state get selected
    @api.onchange('state_id')
    def empty_commune(self):
        for record in self:
            record.commune_id = False
            record.localite_id = False

    #check if localite_id, country_id and state_id are true and fil zip with localite_id.code
    #set zip to False if another country or state or commune get selected
    @api.onchange('localite_id','country_id','state_id')
    def get_zip(self):
        for record in self:
            if record.country_id and record.state_id and record.localite_id:
                record.zip = record.localite_id.code
            else:
                record.update({'zip':False})