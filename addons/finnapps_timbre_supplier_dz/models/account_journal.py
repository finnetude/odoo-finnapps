from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging  as log


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    for_supplier_timbre = fields.Boolean('Pour timbre fournisseur')


    @api.constrains('for_supplier_timbre')
    def constrains_for_supplier_timbre(self):
        if self.for_supplier_timbre and self.env['account.journal'].search([('for_supplier_timbre','=',True), ('id','!=',self.id)]):
            raise ValidationError('Utiliser pour les pièces comptables de type timbre fournisseur ne doit être coché que sur un seul journal.')



