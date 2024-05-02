# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import re
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    name_pc = fields.Char(
        string = 'Libellé',
        compute = "_getnames",

    )

    ref_pc = fields.Char(
        string='Référence',
        compute='_getnames',

    )
    
    residual = fields.Monetary('Résiduel',
        currency_field='company_currency_id',
        compute='_compute_residual',store=True)

    cumulated_residual = fields.Monetary('Résiduel cumulé', store=False,
        currency_field='company_currency_id',
        # compute='_compute_cumulated_residual',
        help="Residual cumulé en fonction du domaine et de l'ordre choisi dans la vue.")

    cumulated_balance = fields.Monetary(string='Solde', store=False,
        currency_field='company_currency_id',
        compute='_compute_cumulated_balance',
        help="Solde cumulé en fonction du domaine et de l'ordre choisi dans la vue.")
    
    def test(self):
        domain = self.env.context.get('default_domain_record')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'finn.imprimer.rapport',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': 'imprimer_livre_tiers_view',
            'views': [[False, 'form']],
            'target': 'new',
            'context':{"default_domain_record": domain},

                   }

    
    @api.depends('move_id')
    def _getnames(self):
        
        for i in self:


            if i.move_id.move_type == 'out_invoice' or i.move_id.move_type == 'in_invoice':
                i.name_pc = "Facture"
                i.ref_pc = i.move_id.name

            elif i.move_id.move_type == 'out_refund' or i.move_id.move_type == 'in_refund':
                i.name_pc = "Avoir"
                i.ref_pc = i.move_id.name


            elif i.payment_id:
                i.name_pc = "Paiement"
                i.ref_pc = i.move_id.name
            else:
                i.name_pc = " "
                i.ref_pc = i.move_id.name
        return
        


    previous_solde = fields.Monetary(string='Solde antérieur',
                                  compute="_compute_previous_solde",)

    current_transaction = fields.Boolean(string="Transaction en cours", compute='_get_booleen_aml',store=True)

    def get_booleen_amls(self):
        amls = self.env['account.move.line'].search([('account_id.account_type', 'in', ['asset_receivable','liability_payable'])])._get_booleen_aml()
    

    @api.depends('date')
    def _get_booleen_aml(self):
        i=0
        for record in self:
            if record.account_id.account_type in ['asset_receivable','liability_payable']:
                aml_record = self.env['account.move.line'].search([('partner_id.id','=',record.partner_id.id),('residual','!=',0),('full_reconcile_id', '=', False)],order = 'date asc', limit=1)
                if aml_record and record.date >= aml_record.date:
                    record.current_transaction = True
                else:
                    record.current_transaction = False
            i+=1

    @api.depends('balance')
    def _compute_previous_solde(self):
        order = self.env.context.get('order_cumulated_balance')

        aml = self.env['account.move.line'].search([('id','in',self.ids)], order=order)
        _logger.info(self.env['account.move.line'])
        n = aml[0].cumulated_balance - (aml[0].debit - aml[0].credit)
        for rec in aml:
            rec.previous_solde = n
            n = rec.cumulated_balance

    def compute_cumulated_balance(self, order, domain, limit=False):
        # get the where clause
        query = self._where_calc(domain)
        sql_order = self._order_to_sql(order, query, reverse=True)
        order_string = self.env.cr.mogrify(sql_order).decode()
        from_clause, where_clause, where_clause_params = query.get_sql()
        if limit :
            sql = """
                SELECT account_move_line.id, SUM(account_move_line.debit - account_move_line.credit)  OVER (
                    ORDER BY %(order_by)s
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )
                FROM %(from)s
                WHERE %(where)s
                LIMIT 1
            """ % {'from': from_clause, 'where': where_clause or 'TRUE', 'order_by': order_string}
        else :
            sql = """
                SELECT account_move_line.id, SUM(account_move_line.debit - account_move_line.credit)  OVER (
                    ORDER BY %(order_by)s
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )
                FROM %(from)s
                WHERE %(where)s
            """ % {'from': from_clause, 'where': where_clause or 'TRUE', 'order_by': order_string}

        self.env.cr.execute(sql, where_clause_params)
        fetched = self.env.cr.fetchall()
        result = {r[0]: r[1] for r in fetched}

        domain_all = []
        for count, elem in enumerate(domain):
            
            if elem[0] == 'partner_id':
                if domain[count -1] in ['|','&'] and count != 1:
                    domain_all.append(domain[count-1])
                domain_all.append(elem)
        
        
        domain_specific =[('full_reconcile_id', '=', False),
                          ('balance','!=', 0), 
                          ('account_id.reconcile','=',True),
                          ('account_id.internal_group', 'in', ['asset_receivable','liability_payable'] ),
                          ('move_id.state','=','posted')
                          ]
        domain_all += domain_specific
        query_all = self._where_calc(domain_all)
        sql_order = self._order_to_sql(order, query_all, reverse=True)
        order_string_all = self.env.cr.mogrify(sql_order).decode()
        from_clause_all, where_clause_all, where_clause_params_all = query_all.get_sql()
        
        sql_all = """
            SELECT account_move_line.id, SUM(account_move_line.balance) OVER (
                ORDER BY %(order_by)s
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )
            FROM %(from)s
            WHERE %(where)s
        """ % {'from': from_clause_all, 'where': where_clause_all or 'TRUE', 'order_by': order_string_all}


        self.env.cr.execute(sql_all, where_clause_params_all)
        fetched_all = self.env.cr.fetchall()
        result_all = {r[0]: r[1] for r in fetched_all}
  
        return result,result_all



    @api.depends_context('order_cumulated_balance', 'domain_cumulated_balance')
    def _compute_cumulated_balance(self):
        domain = self.env.context.get('domain_cumulated_balance')
        order = self.env.context.get('order_cumulated_balance')


        if not domain:
            # Nous ne venons pas de search_read, nous ne sommes donc pas dans une vue de liste, donc cela n'a aucun sens de calculer le solde cumulé
            for record in self:
                record.cumulated_balance = 0
            return

        # get the where clause
        result ,result_all = self.compute_cumulated_balance(order, domain)

        if result != result_all :
            keys = []
            for k in result:
                keys.append(k)

            move_lines = self
            first = True

            epsilon = 0
            for record in move_lines:

                if first:
                    if record.id in result_all:     
                        epsilon = result_all[record.id] - result[record.id] 
                        record.cumulated_balance = result_all[record.id] 
                    else:
                        epsilon = 0
                        record.cumulated_balance = result[record.id] 
                    first = False
                else :
                    record.cumulated_balance = epsilon + result[record.id]
        else:
            for record in self:
                record.cumulated_balance = result[record.id]



    @api.depends('matched_credit_ids','matched_debit_ids','credit','debit')
    def _compute_residual(self):
        for record in self:
            if record.account_id.account_type in ['asset_receivable','liability_payable']:
                credit = 0
                debit = 0
                if record.credit > 0:
                    for r in record.matched_debit_ids:
                        debit += r.amount
                    credit += record.credit
                else:
                    for r in record.matched_credit_ids:

                        credit += r.amount
                    debit += record.debit

                record.residual = debit - credit
            else :
                record.residual = 0



class AccountMove(models.Model):
    _inherit = "account.move"


    def action_post(self ):
        res = super(AccountMove, self).action_post()
        for line in self.line_ids:
            line.partner_id.get_the_solde()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for line in self.line_ids:
            line.partner_id.get_the_solde()
        return res

    def action_invoice_print(self):
        
      
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('account.account_invoices').report_action(self)
        else:
            return self.env.ref('account.account_invoices_without_payment').report_action(self)

