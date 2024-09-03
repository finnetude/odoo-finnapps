from odoo import models, fields, api

class HrLeave(models.Model):

    _inherit = 'hr.leave'

    return_to_work_date = fields.Date(
    	string="Date de reprise de travail"
    	)


    #Pour affichier le boutton d'impression de titre de congé seulement 
    # au niveau des type de congé où le champ 'Permettre l'impression d'un titre de congé' est coché
    leave_entitlement = fields.Boolean(
    	related="holiday_status_id.print_entitlement_leave"
    	)


    
