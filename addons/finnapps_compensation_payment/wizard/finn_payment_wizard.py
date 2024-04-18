# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging as log


class FinnScanWizard(models.TransientModel):
    _name = 'finn.compensation.payment.wizard'

    # Fonction de récupération de la devise de la société de l'utilisateur
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

   

    # Fonction de récupération du montant dû de la facture fournisseur
    @api.depends('supplier_invoice_id')
    def _get_du_amount(self):
        self.du_amount = self.supplier_invoice_id.amount_residual if self.supplier_invoice_id else 0.0

    # Fonction de calcule du montant de la compensation
    @api.depends('supplier_invoice_id')
    def _get_compensation_amount(self):
        if self._context.get('active_id'):
            related_invoice = self.env['account.move'].browse([self._context.get('active_id')])
            if related_invoice:
                self.compensation_amount = self.supplier_invoice_id.amount_residual if self.supplier_invoice_id.amount_residual <= related_invoice.amount_residual else related_invoice.amount_residual


    supplier_invoice_id = fields.Many2one(
        'account.move',
        string=_('Facture fournisseur'),
        required=True,
        )

    invoice_id = fields.Many2one(
        'account.move',
        )



        
    du_amount = fields.Monetary(
        string=_('Montant dû'),
        required=True,
        compute='_get_du_amount'
        )

    compensation_amount = fields.Monetary(
        string=_('Montant de compensation'),
        required=True,
        compute='_get_compensation_amount'
        )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        readonly=True,
        default=_default_currency
        )

    partner_id = fields.Many2one(
        'res.partner',
        string="Client",
        related="invoice_id.partner_id"
        )

    def post(self):

        account_move = self.env['account.move']

        inv = self.env['account.move'].browse([self._context.get('active_id')])

        if inv:
            name = self.env['ir.sequence'].next_by_code('paiement.compensation.seq')
            
            journal_id = self.env['account.journal'].search([('compensation_journal','=',True)], limit=1)
            if not journal_id:
                raise ValidationError('Veuillez choisir un journal a utiliser pour le paiement par compensation.')

            move_vals = {
                    'name': name, 
                    'ref': inv.ref,
                    'journal_id': journal_id.id,
                    'date': datetime.today(), 
                    
                }

            move = account_move.create(move_vals) # créer la pièce comptable

            debit_moves = self._create_aml_lines(self.compensation_amount, 0.0, self.supplier_invoice_id, move) # créer debit line pour la pièce
            credit_moves = self._create_aml_lines(0.0, self.compensation_amount, inv, move) # créer crédit line pour la pièce
            
            move.action_post()
            self._partial_reconcile(inv, debit_moves, credit_moves)

            if self.supplier_invoice_id.id not in inv.compensation_invoice_ids.ids:
                inv.compensation_invoice_ids = [(4, self.supplier_invoice_id.id)]
                inv.total_compensation += self.compensation_amount

            return """ {
                'type': 'ir.actions.act_window',
                'name': ('Pièces Comptable'),
                'res_model': 'account.move',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': move.id,
            }"""

    def _create_aml_lines(self, debit=0.0, credit=0.0, inv=False, move=False):

        aml_model = self.env['account.move.line']
        for line in inv.line_ids:
            if line.account_id.account_type in ['asset_receivable','liability_payable']:
                account = line.account_id.id
        vals = {
                'name': _('Compensation débit') if debit else _('Compensation crédit'),
                'debit': debit,
                'credit': credit,
                # 'account_id': inv.account_id.id if credit else self.supplier_invoice_id.line_ids.account_id.id,
                'account_id': account,
                'move_id': move.id if move else False,
                # 'currency_id': self.currency_id.id,
                # 'amount_currency': 0.0,
                'partner_id': inv.partner_id.id,
            }
        res = aml_model.with_context(check_move_validity=False).create(vals)
        return res

    def _partial_reconcile(self, inv, debit_moves, credit_moves):
        """
            - Léttrer l'écriture comptable(en débit) de la pièce généré avec l'écriture de la facture fournisseur(en débit)
            - Léttrer l'écriture comptable(en crédit) de la pièce généré avec l'écriture de la facture client(en crédit)
        """
        # lettrage pour les écritures de la facture fournisseur
        if debit_moves and self.supplier_invoice_id:
            aml = self.supplier_invoice_id.line_ids.filtered(lambda x: x.account_id.id == debit_moves.account_id.id)
            if aml:
                s = debit_moves + aml
                s.reconcile()
                

        # lettrage pour les écritures de la facture client
        if credit_moves and inv:
            aml = inv.line_ids.filtered(lambda x: x.account_id.id == credit_moves.account_id.id)
            if aml:
                s = credit_moves + aml
                s.reconcile()
                
