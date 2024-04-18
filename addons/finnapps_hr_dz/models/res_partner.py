from odoo import models, fields, api

class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_cnas_agency = fields.Boolean("Est une agence CNAS")

    agency_code = fields.Integer('Code de l\'agence')

    code_adherant = fields.Char(string="Code d'adhérant")
    
    is_payment_center = fields.Boolean(string="Est un centre de paiement")
    
    declaration_type = fields.Selection(
            [('1', 'Mensuel'), 
            ('2', 'Trimestriel')], 
            string="Type de déclaration",
        )

    @api.onchange('company_type')
    def _onchange_is_cnas_agency(self):
        if self.company_type == "person":
            self.is_cnas_agency = False

    @api.onchange('is_cnas_agency')
    def _onchange_is_payment_center(self):
        if self.is_cnas_agency == True:
            self.is_payment_center = False
            self.declaration_type = False