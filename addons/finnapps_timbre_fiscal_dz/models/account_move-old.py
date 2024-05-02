# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from contextlib import ExitStack, contextmanager
from odoo.exceptions import ValidationError, UserError
from odoo.tools import frozendict ,format_amount
import logging
import inspect




class AccountInvoice(models.Model):
    _inherit = 'account.move'

    payment_mode = fields.Many2one(
        'finn.account.payment.mode',
        string="Mode de paiement",
    )

    amount_timbre = fields.Monetary(
        string='Droit de timbre',
        readonly=True,
        compute='_compute_amount_timbre'
    )

    total_timbre = fields.Monetary(
        string='Montant avec timbre',
        readonly=True,
        compute='_compute_amount_timbre'
    )

    payment_mode_type = fields.Char("Type")

    montant_en_lettre = fields.Boolean(
        string="Afficher le montant en lettre sur l’impression des factures",
        compute='get_timbre_montant_en_lettre',
    )

    needed_timbre = fields.Binary(compute='_compute_needed_timbre')
    needed_timbre_dirty = fields.Boolean(compute='_compute_needed_timbre')
    
    based_on_related = fields.Selection(string='Based', related="company_id.based_on")


    @api.onchange('payment_mode')
    def _onchange_payment_mode(self):
        for record in self:
            if record.payment_mode.finn_mode_type == 'cash':
                if not record.company_id.sale_timbre :
        
                    raise ValidationError(_('Verifier si les comptes contrepartie sont rempli sur la configuration de timbre'))

            record.payment_mode_type = record.payment_mode.finn_mode_type if record.payment_mode else False





    def _timbre(self, amount_total):
        timbre = 0.0
        if self.payment_mode and self.payment_mode.finn_mode_type == "cash":
            timbre = int(self.company_id._timbre(amount_total))
        return timbre

    @api.depends('amount_total','payment_mode','invoice_line_ids','invoice_payment_term_id')
    def _compute_amount_timbre(self):
        for record in self:
            # Compute amount_total
            total_tax_currency = 0.0 
            amount_total = 0.0

            # The amount total is calculated when the new vals are writted ,so in this compute amount_total is still 0 
            # the visible amounts are actually a widget calculated on js for show only  
            for line in record.invoice_line_ids:
                if record.is_invoice(True):
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        amount_total += line.amount_currency

                    elif line.display_type in ('product', 'rounding'):
                        amount_total += line.price_total

                 
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        amount_total += line.amount_currency


            if record.payment_mode.finn_mode_type != 'cash':
                record.amount_timbre = 0
                
            else :
                record.amount_timbre = int(record._timbre(amount_total))
            record.total_timbre = amount_total + record.amount_timbre if record.amount_timbre else 0.0


 
    # With this the new line of timber is created/edited
    @api.depends('invoice_date_due', 'currency_id', 'amount_timbre','invoice_payment_term_id')
    def _compute_needed_timbre(self):
        
        for invoice in self:
            invoice.needed_timbre = {}
            invoice.needed_timbre_dirty = True
            if invoice.is_invoice(True) and invoice.company_id.based_on == 'posted_invoices' and invoice.payment_mode and invoice.payment_mode.finn_mode_type == 'cash':
      
                account_timbre_id  = invoice.company_id.sale_timbre
                invoice.needed_timbre = {
                frozendict({
                    'move_id': invoice.id,
                    'account_id': account_timbre_id.id,
                    'display_type': 'timbre',
                    'date_maturity': invoice.invoice_date_due ,
                    


                    }): {
                    'name': 'Timbre' if invoice.move_type == 'out_invoice' else 'Droit de timbre',
                    'quantity': 1.0,
                    'currency_id': invoice.currency_id.id ,
                    'balance': -1 * invoice.amount_timbre ,
                    'amount_currency': -1 * invoice.amount_timbre ,
                    'account_id': account_timbre_id.id,
                    'display_type': 'timbre',
                    'date_maturity': invoice.invoice_date_due ,

                    }

                }

    # override the function that create/edit line of terms
    @api.depends('invoice_payment_term_id', 'invoice_date', 'currency_id', 'amount_total_in_currency_signed', 'invoice_date_due','payment_mode')
    def _compute_needed_terms(self):
        for invoice in self:
            invoice.needed_terms = {}
            invoice.needed_terms_dirty = True
            sign = 1 if invoice.is_inbound(include_receipts=True) else -1
            if invoice.is_invoice(True):
                if invoice.invoice_payment_term_id:
                    invoice_payment_terms = invoice.invoice_payment_term_id._compute_terms(
                        date_ref=invoice.invoice_date or invoice.date or fields.Date.today(),
                        currency=invoice.currency_id,
                        tax_amount_currency=invoice.amount_tax * sign,
                        tax_amount=invoice.amount_tax_signed,
                        untaxed_amount_currency=invoice.amount_untaxed * sign,
                        untaxed_amount=invoice.amount_untaxed_signed,
                        company=invoice.company_id,
                        sign=sign
                    )
                    
                    for term_line in invoice_payment_terms['line_ids']:
                        key = frozendict({
                            'move_id': invoice.id,
                            'date_maturity': fields.Date.to_date(term_line.get('date')),
                            'discount_date': invoice_payment_terms.get('discount_date'),

                        })
                        # add the value of amount_timbre to keep th balance 
                        values = {
                            'balance': term_line['company_amount']+ invoice.amount_timbre if invoice.company_id.based_on == 'posted_invoices' else term['company_amount'] ,
                            'amount_currency': term_line['foreign_amount']+ invoice.amount_timbre if invoice.company_id.based_on == 'posted_invoices' else term['foreign_amount'] ,
                            'discount_date': invoice_payment_terms.get('discount_date'),
                            'name': invoice.payment_reference or '',
                            'discount_amount_currency': invoice_payment_terms.get('discount_amount_currency') or 0.0,
                            'discount_balance': invoice_payment_terms.get('discount_balance') or 0.0,
                        }
                        if key not in invoice.needed_terms:
                            invoice.needed_terms[key] = values
                        else:
                            invoice.needed_terms[key]['balance'] += values['balance']
                            invoice.needed_terms[key]['amount_currency'] += values['amount_currency']
                else:

                    # add the value of amount_timbre to keep th balance 
                    invoice.needed_terms[frozendict({
                        'move_id': invoice.id,
                        'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
                        'discount_date': False,
                        'discount_balance': 0.0,
                        'discount_amount_currency': 0.0
                    })] = {
                        'balance': invoice.amount_total_signed + invoice.amount_timbre if invoice.company_id.based_on == 'posted_invoices' else invoice.amount_total_signed,
                        'amount_currency': invoice.amount_total_in_currency_signed + invoice.amount_timbre if invoice.company_id.based_on == 'posted_invoices' else invoice.amount_total_in_currency_signed ,
                        'name': invoice.payment_reference or '',
                    }
    


    @api.depends('payment_mode')
    def get_timbre_montant_en_lettre(self):
        for record in self:
            logic = False

            if record.payment_mode and record.payment_mode.finn_mode_type == "cash":
                logic = self.company_id.montant_en_lettre
            record.montant_en_lettre = logic
           
    def custom_amount_to_text(self, montant):
        currency_id = self.currency_id or self.env.ref('base.DZD')
        res = currency_id.amount_to_text(montant)
        if round(montant % 1, 2) == 0.0:
            res += " et zéro centime"
        if montant > 1.0:
            res = res.replace('Dinar', 'Dinars')
        return res.lower().capitalize()


    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'amount_timbre')
    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0


            for line in move.line_ids:

                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
      
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign
            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)
            # Compute total_timbre
          #  move.total_timbre = move.amount_total + move.amount_timbre if move.amount_timbre else 0.0


  

    # override the original function
    @contextmanager
    def _sync_dynamic_lines(self, container):
        with self._disable_recursion(container, 'skip_invoice_sync') as disabled:
            if disabled:
                yield
                return
            # Only invoice-like and journal entries in "auto tax mode" are synced

            # tax_filter
            tax_filter = lambda m: (m.is_invoice(True) or m.line_ids.tax_ids and not m.tax_cash_basis_origin_move_id)
            invoice_filter = lambda m: (m.is_invoice(True))
            misc_filter = lambda m: (m.move_type == 'entry' and not m.tax_cash_basis_origin_move_id)

            # timbre_filter
            timbre_filter = lambda m: (m.payment_mode.finn_mode_type == 'cash' and m.company_id.based_on == "posted_invoices")
            tax_container = {'records': container['records'].filtered(tax_filter)}
            invoice_container = {'records': container['records'].filtered(invoice_filter)}
            misc_container = {'records': container['records'].filtered(misc_filter)}

            # timbre_container
            timbre_container = {'records': container['records'].filtered(timbre_filter)}


            with ExitStack() as stack:

                stack.enter_context(self._sync_dynamic_line(
                    existing_key_fname='term_key',
                    needed_vals_fname='needed_terms',
                    needed_dirty_fname='needed_terms_dirty',
                    line_type='payment_term',
                    container=invoice_container,
                ))

        
                stack.enter_context(self._sync_unbalanced_lines(misc_container))

                stack.enter_context(self._sync_rounding_lines(invoice_container))


                stack.enter_context(self._sync_dynamic_line(
                    existing_key_fname='tax_key',
                    needed_vals_fname='line_ids.compute_all_tax',
                    needed_dirty_fname='line_ids.compute_all_tax_dirty',
                    line_type='tax',
                    container=tax_container,
                ))


                # This will create/edit the line of timbre
                stack.enter_context(self._sync_dynamic_line(
                    existing_key_fname='timbre_key',
                    needed_vals_fname='needed_timbre',
                    needed_dirty_fname='needed_timbre_dirty',
                    line_type='timbre',
                    container=timbre_container,
                ))


                stack.enter_context(self._sync_dynamic_line(
                    existing_key_fname='epd_key',
                    needed_vals_fname='line_ids.epd_needed',
                    needed_dirty_fname='line_ids.epd_dirty',
                    line_type='epd',
                    container=invoice_container,
                ))

                stack.enter_context(self._sync_invoice(invoice_container))

              
                line_container = {'records': self.line_ids}
                with self.line_ids._sync_invoice(line_container):
                    yield
                    line_container['records'] = self.line_ids
                tax_container['records'] = container['records'].filtered(tax_filter)
                invoice_container['records'] = container['records'].filtered(invoice_filter)
                misc_container['records'] = container['records'].filtered(misc_filter)

                # update timbre container
                timbre_container['records'] = container['records'].filtered(timbre_filter)


            # Delete the tax lines if the journal entry is not in "auto tax mode" anymore
            for move in container['records']:
                if move.move_type == 'entry' and not move.line_ids.tax_ids:
                    move.line_ids.filtered(
                        lambda l: l.display_type == 'tax'
                    ).with_context(dynamic_unlink=True).unlink()

                # Delete timbre line 
                if move.payment_mode.finn_mode_type != 'cash' or move.amount_timbre == 0 or move.line_ids.filtered(lambda l: l.display_type == 'timbre' and l.balance != -1* move.amount_timbre):
             
                    move.line_ids.filtered(
                        lambda l: l.display_type == 'timbre' and l.balance != -1* move.amount_timbre or l.balance == 0
                    ).with_context(dynamic_unlink=True).unlink()





class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    timbre_key = fields.Binary(compute='_compute_timbre_key')

    display_type = fields.Selection(
        selection_add=[
            ('timbre', 'Timbre'),
        ],
        ondelete= {'timbre': 'cascade'},
    )

    # this will verify if the line timbre exist or not
    @api.depends('date_maturity')
    def _compute_timbre_key(self):

        for line in self:
            if line.display_type == 'timbre' and line.company_id.based_on == 'posted_invoices':
                account_timbre_id  = self.company_id.sale_timbre
                line.timbre_key = frozendict({
                    'account_id': line.account_id.id,
                    'move_id': line.move_id.id,


                })
            else:
                line.timbre_key = False
       

    #Override original function
    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                amount = sign * line.price_unit / line.currency_rate * (1 - line.discount / 100)
                handle_price_include = True
                quantity = line.quantity
                date_maturity=fields.Date.today(),

            # if it's a timbre line don't add it to the tax compute
            elif line.display_type == 'timbre':
                amount_currency = 0
                amount = 0
                handle_price_include = False
                quantity = 0
                
            else:
                amount_currency = line.amount_currency
                amount = line.balance
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,

                }): {
                    'name': tax['name'],
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }
    
    

