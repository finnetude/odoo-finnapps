from odoo import models, fields, api

class FinnMovementEmployees(models.Model):
    _name = "finn.movement.employees"
    _description = "Mouvement des salariés"

    employee_id = fields.Many2one("hr.employee", "Nom & Prénom")
    name = fields.Char("Numéro", related= 'employee_id.ssnid')
    company_id = fields.Many2one('res.company', 'Société', required=True, index=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True, related='company_id.currency_id')
    emp_birthday = fields.Date(string='Date de naissance', related='employee_id.birthday')
    output_input = fields.Char("E/S")
    date_out_input = fields.Date("Date E/S")
    observation = fields.Char("Observation")
    employee_agency = fields.Char("Agence d'employée")
    
    
    employee_movement_id = fields.Many2one('finn.declaration.cotisation', string='Mouvement des salariés')