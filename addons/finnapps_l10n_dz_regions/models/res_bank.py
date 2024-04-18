# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class ResBank(models.Model):
    _inherit = 'res.bank'

    commune_id = fields.Many2one(
        "finn.res.country.state.commune",
        'Commune',
        domain="[('state_id','=',state)]"
    )

    localite_id = fields.Many2one(
        "finn.res.country.state.localite",
        'Localité',
        domain="[('state_id','=',state)]"
    )

    

    country_id = fields.Many2one(
        'res.country',
        'Pays',
        required=True,
        related='state.country_id'
        )

    code = fields.Char(
        'Code Commune',
        size=5,
        help='Le code de la commune sur deux positions.',
        required=True
    )

    #set state_id to False if another country get selected
    @api.onchange('country_id')
    def empty_state(self):
        for record in self:
            record.state = False

    #set commune_id to False if another state get selected
    @api.onchange('state')
    def empty_commune(self):
        for record in self:
            record.commune_id = False
            record.localite_id = False

    #check if localite_id, country_id and state_id are true and fil zip with communelocalite_id_id.code
    #set zip to False if another country or state or commune get selected
    @api.onchange('localite_id','country_id','state')
    def get_zip(self):
        for record in self:
            if record.country and record.state and record.localite_id:
                record.zip = record.localite_id.code
            else:
                record.update({'zip':False})


