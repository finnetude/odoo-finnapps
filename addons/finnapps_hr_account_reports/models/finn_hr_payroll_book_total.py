from odoo import models, fields, api, _

class FinnHrPayrollBook(models.Model):
    _name = "finn.hr.payroll.book.total"
    _order = 'sequence asc'
    _description = "Livre de paie/État des prestations des services"
    
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)

    code = fields.Char('Code')

    name = fields.Char('Nom')

    sequence = fields.Integer('Séquence')

    total = fields.Float('Total de la rubrique')
