from odoo import models, fields, api

class HrLeaveType(models.Model):

    _inherit = 'hr.leave.type'

    print_entitlement_leave = fields.Boolean(
    	string="Permettre l'impression d'un titre de congé"
    	)
