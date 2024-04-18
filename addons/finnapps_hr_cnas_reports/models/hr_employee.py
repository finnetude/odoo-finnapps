from odoo import models, fields

class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    family_name = fields.Char('Nom de famille')
    surname = fields.Char('Prénom')


    
