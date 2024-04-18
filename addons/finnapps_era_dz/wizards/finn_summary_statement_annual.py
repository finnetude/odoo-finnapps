# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
import logging as log

class FinnSummaryStatementAnnual(models.TransientModel):
    _name = 'finn.summary.statement.annual'
    _description = "État récapitulatif annuel"

    name = fields.Char('Nom')

    fiscalyear_id = fields.Many2one('finn.exercice', 'Exercice comptable' )

    date_start = fields.Date('Date début', compute="_compute_date", readonly=False)
    date_end = fields.Date('Date fin', compute="_compute_date", readonly=False)

    company_id = fields.Many2one('res.company', 'Société', default= lambda self : self.env.company )
    currency_id = fields.Many2one('res.currency', 'Devise' ,related='company_id.currency_id')
    date_now = fields.Date(default=fields.Date.today)
    ssa_line_ids = fields.One2many('finn.summary.statement.annual.line','ssa_id', 'Ligne d\'état récapitulatif annuel' )

    @api.depends('fiscalyear_id')
    def _compute_date(self):
        if self.fiscalyear_id:
            self.date_start = self.fiscalyear_id.date_from
            self.date_end = self.fiscalyear_id.date_to
        else:
            self.date_start = False
            self.date_end = False


    def calculate_ssa_lines(self):
        self.ssa_line_ids.unlink()
        lst = []
        configs = self.env['finn.summary.statement.config'].search([])
        for config in configs:
            ##### Récuperer les comptes #######################################
            account_include = account_exclude = self.env['account.account']

            acc_list_include = eval(config.accounts)
            if acc_list_include:
                domain_include = ['|' for i in range(1,len(acc_list_include))]
                for a in acc_list_include:
                    domain_include.append(('code','ilike',str(a)+'%'))
                
                account_include = self.env['account.account'].search(domain_include)

            
            acc_list_exclude = eval(config.accounts_to_exclude)
            if acc_list_exclude :
                domain_exclude = ['|' for i in range(1,len(acc_list_exclude))]
                for a in acc_list_exclude:
                    domain_exclude.append(('code','ilike',str(a)+'%'))
            
                account_exclude = self.env['account.account'].search(domain_exclude)

            accounts = account_include - account_exclude
            ####################################################################
            move_lines = self.env['account.move.line'].search([
                ('account_id','in', accounts.ids),
                ('date','<=',self.date_end),
                ('date','>=',self.date_start)
                ])
            
            total = sum(move_lines.mapped('credit')) + sum(move_lines.mapped('debit'))
       
            lst.append({
                'name': config.designation,
                'amount' : total,
                })
        for l in lst:
            self.ssa_line_ids += self.ssa_line_ids.create(l)
        
        return {
            'name': "État récapitulatif annuel",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'finn.summary.statement.annual',
            'view_id': self.env.ref('finnapps_era_dz.summary_statement_annual_view').id,
            'context': {
                'default_fiscalyear_id': self.fiscalyear_id.id,
                'default_date_start': self.date_start,
                'default_date_end': self.date_end,
                'default_ssa_line_ids': self.ssa_line_ids.ids,
            },
            'target': 'new',
        }



    def print_report(self):
        return self.env.ref('finnapps_era_dz.action_sumstate_annual').report_action(self)



class FinnSummaryStatementAnnualLine(models.TransientModel):
    _name = 'finn.summary.statement.annual.line'
    _description = "Lignes de l'État récapitulatif"

    name = fields.Char('Nom')
    amount = fields.Monetary('Montant')
    company_id = fields.Many2one('res.company', 'Société', default= lambda self : self.env.company )
    currency_id = fields.Many2one('res.currency', 'Devise' ,related='company_id.currency_id')
    ssa_id = fields.Many2one('finn.summary.statement.annual')