from odoo import models, fields

class ResCompany(models.Model):

    _inherit = 'res.company'

    activite = fields.Char('Activité', size=64, default="My company activity")
