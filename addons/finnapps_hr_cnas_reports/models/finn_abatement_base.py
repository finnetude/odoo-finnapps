from odoo import models, fields, api

class FinnAbatementBase(models.Model):
    _name = "finn.abatement.base"
    _description = "Assiette d'abattement"

    employee_id = fields.Many2one("hr.employee", "Nom & Prénom")
    name = fields.Char("Numéro", related= 'employee_id.ssnid')
    company_id = fields.Many2one('res.company', string ='Société', required=True, index=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True, related='company_id.currency_id')
    emp_birthday = fields.Date(string='Date de naissance', related='employee_id.birthday')
    base = fields.Monetary(string='Assiette')
    justification = fields.Char('Justification')
    abatement_type = fields.Selection(
        [('a40', 'Abattement 40%'),
         ('a80', 'Abattement 80%'),
         ('a90', 'Abattement 90%')],
        "Type d'abattement", compute ='_compute_type_abattement'
        )

    abatement40_id = fields.Many2one('finn.declaration.cotisation', string='Abattement 40%')
    abatement80_id = fields.Many2one('finn.declaration.cotisation', string='Abattement 80%')
    abatement90_id = fields.Many2one('finn.declaration.cotisation', string='Abattement 90%')
    

    @api.onchange("employee_id.nat_cot1")
    def _compute_type_abattement(self):
        for rec in self:
            if rec.employee_id.nat_cot1 == 'R06':
                rec.abatement_type = ('a40')
            if rec.employee_id.nat_cot1 == 'R07':
                rec.abatement_type = ('a80')
            if rec.employee_id.nat_cot1 == 'R08':
                rec.abatement_type = ('a90')

