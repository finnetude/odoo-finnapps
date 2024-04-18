from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    advantage_ids = fields.Many2many('finn.hr.bonuse.advantage', 'hr_advantage_employee_employee', 'employee_id', 'advantage_employee_id', string='Aventages de la paie')

class HrContract(models.Model):
    _inherit = 'hr.contract'

    advantage_ids = fields.Many2many('finn.hr.bonuse.advantage', 'hr_advantage_employee_contract', 'contract_id', 'advantage_contract_id', string='Aventages de la paie')

class HrContract(models.Model):
    _inherit = 'hr.job'

    advantage_ids = fields.Many2many('finn.hr.bonuse.advantage', 'hr_advantage_employee_hr_job', 'job_id', 'advantage_job_id', string='Aventages de la paie')
