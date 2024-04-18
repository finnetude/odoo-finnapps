from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'
  
    purchase_offset_account = fields.Many2one('account.account', string ="Compte contrepartie achat",)