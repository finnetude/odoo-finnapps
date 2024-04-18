from odoo import models, fields, api

class FinnFormeJuridique(models.Model):

    _name = 'finn.forme.juridique'
    _description = "Formes juridique"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code")

    @api.depends('code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = (record.code and (record.code + ' - ') or '') + record.name

    @api.model
    def create_fj_records(self):
        fj = self.env['finn.forme.juridique']
        vals = [
            {'code': 'SARL', 'name': 'Société à responsabilité limitée'},
            {'code': 'EURL', 'name': 'Société unipersonnelle à responsabilité limitée'},
            {'code': 'Entreprise Individuelle', 'name': 'Entreprise Individuelle'},
            {'code': 'SPA', 'name': 'Société par actions'},
            {'code': 'SNC', 'name': 'Société en nom collectif'},
            {'code': 'SCS', 'name': 'Société en commandite simple'},
            {'code': 'SCPA', 'name': 'Société en commandite par actions'},
            {'code': 'Groupement','name': 'Groupement'},
        ]
        for val in vals:
            if not fj.search([('code','=',val['code'])]):
                fj.create(val)