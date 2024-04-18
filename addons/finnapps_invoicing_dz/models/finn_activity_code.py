from odoo import models, fields, api

class FinnActivityCode(models.Model):
    
    _name = "finn.activity.code"
    _description = "Code d'activité"

    name            = fields.Char(string="Nom", required = True,index=True)
    code            = fields.Integer(string="Code", required = True, index=True)
    company_id      = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company.id)
    
    is_principal    = fields.Boolean(string="Code principal")
    regulation      = fields.Selection([('none', 'Aucune réglementation'),
                                        ('regulated_activity', 'Activité réglementée'),
                                        ('unauthorized_activity', 'Activité non autorisée')],
                                        string="Réglementation", default='none')

    @api.depends('code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = (str(record.code) and (str(record.code) + ' - ') or '') + record.name

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            domain = ['|',('name', operator, name),('code', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)
