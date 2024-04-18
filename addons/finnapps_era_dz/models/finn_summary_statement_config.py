# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import  ValidationError

class FinnSummaryStatementConfig(models.Model):
    _name = 'finn.summary.statement.config'
    _description = "Configuration de l'État récapitulatif"

    name = fields.Char('Nom')

    sequence = fields.Integer('Séquence')
    designation = fields.Char('Désignation')
    accounts = fields.Char('Comptes',default="[]")
    accounts_to_exclude = fields.Char('Comptes à exclure',default="[]")
    
    company_id = fields.Many2one('res.company', 'Société', default= lambda self : self.env.company )

    @api.constrains('accounts')
    def constrains_accounts(self):
        if not self.accounts:
            self.accounts = '[]'
        if self.accounts[0]!= '[' or self.accounts[-1]!= ']' :
            raise ValidationError(_('Format doit etre une liste [ , ,]'))
    
    @api.constrains('accounts_to_exclude')
    def constrains_accounts(self):
        if not self.accounts_to_exclude:
            self.accounts_to_exclude = '[]'
        if self.accounts_to_exclude[0]!= '[' or self.accounts_to_exclude[-1]!= ']' :
            raise ValidationError(_('Format doit etre une liste [ , ,]'))
   
