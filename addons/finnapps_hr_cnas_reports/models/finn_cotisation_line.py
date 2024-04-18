from odoo import models, fields, api

class FinnDeclarationCotisationLine(models.Model):
    _name = "finn.cotisation.line"

    line_cotisation_id = fields.Many2one('finn.declaration.cotisation', string='Décalration de cotisation')

    code = fields.Char('Code')

    nature_cotisation = fields.Char('Nature des cotisation')

    assiette = fields.Float('Assiette' ,digits = (12,2))

    taux = fields.Float('Taux')

    amount = fields.Float('Montant', compute="_calcule_amount",digits = (12,2))

    company_id = fields.Many2one('res.company', string='Société', required=True, index=True)
    
    @api.depends("taux","assiette")
    def _calcule_amount(self):
        for record in self:
            record.amount = record.assiette * record.taux / 100

    @api.onchange('line_cotisation_id')
    def onchange_company_id(self):
        self.company_id = self.line_cotisation_id.company_id

