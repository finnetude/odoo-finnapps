from odoo import models, fields

class ResPartner(models.Model):

    _inherit = 'res.partner'

    activity_code_id = fields.Many2many('finn.activity.code', string ="Code d'activité", help="Si vous avez plusieurs codes d'activtés, il faut choisir un comme un code principal de la société en cochant le champ 'C'est le code principal'")
