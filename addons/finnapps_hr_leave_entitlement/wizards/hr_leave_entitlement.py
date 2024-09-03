from odoo import models, fields, api, _
import logging as log



class HrLeaveEntitlement(models.TransientModel):

    _name = 'hr.leave.entitlement'
    _description= "Titre de congé"


    leave_id = fields.Many2one(
        'hr.leave', 
        string="Congé", 
        readonly=True
        )

    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employé", 
        )

    employee_ids = fields.Many2many(
        'hr.employee', 
        string="Employés",
        related="leave_id.employee_ids" 
        )

    employee_allocation = fields.Float(
        string="Nombre de jours calendaires",
        compute="compute_employee_allocation"
        )

    reliquat = fields.Float(
        string="Reliquat",
        compute="compute_reliquat"
        )

    address_during_leave = fields.Char(
        string="Adresse durant le congé"
        )

    @api.depends('employee_id')
    def compute_employee_allocation(self):
        for record in self:
            record.employee_allocation = 0.0
            a = 0
            
            if record.employee_id:
                tageted_allocation = self.env['hr.leave.allocation'].search([('employee_id','=',record.employee_id.id)])
                for alloc in tageted_allocation:
                    a+= alloc.number_of_days_display
                    record.employee_allocation = a
            else:
                record.employee_allocation = 0.0



    @api.depends('employee_id','employee_allocation')
    def compute_reliquat(self):
        for record in self:
            record.reliquat = 0.0
            if record.employee_allocation and record.employee_id:
                record.reliquat = record.employee_allocation - record.leave_id.number_of_days_display
            else:
                record.reliquat = 0.0


    







    def print_leave_entitlement(self):
        return self.env.ref("finnapps_hr_leave_entitlement.action_hr_leave_entitlement_report").report_action(self)