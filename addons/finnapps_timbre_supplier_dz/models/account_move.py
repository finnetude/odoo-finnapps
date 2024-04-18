from odoo import models, fields, api, _
from contextlib import ExitStack, contextmanager
from odoo.exceptions import ValidationError, UserError
from odoo.tools import frozendict ,format_amount
import logging  as log


class AccountMove(models.Model):
    _inherit = 'account.move'

    
    payment_mode_supplier = fields.Many2one(
        'finn.account.payment.mode',
        string="Mode de paiement",
        
    )

    payment_mode_supplier_type = fields.Selection(related='payment_mode_supplier.finn_mode_type')

    amount_timbre_supplier = fields.Monetary(string = "Droit de timbre", digits = (2))
    amount_with_timbre_supplier = fields.Monetary(string = "Montant avec timbre",compute='_compute_amount_timbre_supplier' , digits = (2))
    
    """Un champ boolean utilisé pour la visibilté d'autre champs en fonction de la valeur de champ  'Se basé sur' """
    for_based_on_in_move = fields.Boolean(string="Pour le champ 'Se basé sur'")


    needed_timbre_supplier = fields.Binary(compute='_compute_needed_timbre_supplier')
    needed_timbre_supplier_dirty = fields.Boolean(compute='_compute_needed_timbre_supplier')


    @api.onchange('for_based_on_in_move')
    def onchange_for_based_on(self):
        if self.company_id.based_on == "posted_invoices":
            self.for_based_on_in_move = True
        else:
            self.for_based_on_in_move = False



    @api.onchange('payment_mode_supplier','amount_timbre_supplier')
    def onchange_amount_timbre_supplier(self):
        if self.payment_mode_supplier.finn_mode_type != "cash":
            self.amount_timbre_supplier = 0.0



    @api.depends('amount_total','payment_mode_supplier','amount_timbre_supplier','invoice_line_ids','invoice_payment_term_id')
    def _compute_amount_timbre_supplier(self):
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
                        amount_total += line.price_subtotal
                 
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        amount_total += line.amount_currency

   
            record.amount_with_timbre_supplier = amount_total + record.amount_timbre_supplier 
     


    # With this the new line of timber is created/edited
    @api.depends('invoice_date_due', 'currency_id', 'amount_timbre_supplier','invoice_payment_term_id')
    def _compute_needed_timbre_supplier(self):
        
        for invoice in self:
            invoice.needed_timbre_supplier = {}
            invoice.needed_timbre_supplier_dirty = True

            if invoice.is_invoice(True) and invoice.for_based_on_in_move == True and invoice.payment_mode_supplier and invoice.payment_mode_supplier.finn_mode_type == 'cash': 
      
                account_timbre_id  = invoice.company_id.purchase_offset_account 
                invoice.needed_timbre_supplier = {
                frozendict({
                    'move_id': invoice.id,
                    'account_id': account_timbre_id.id,


                    }): {
                    'name': 'Droit de timbre fournisseur',
                    'quantity': 1.0,
                    'currency_id': invoice.currency_id.id ,
                    'balance': invoice.amount_timbre_supplier ,
                    'amount_currency':  invoice.amount_timbre_supplier ,
                    'account_id': account_timbre_id.id,
                    'display_type': 'timbre',

                    }

                }
  
    # override the function that create/edit line of terms
    @api.depends('invoice_payment_term_id', 'invoice_date', 'currency_id', 'amount_total_in_currency_signed', 'invoice_date_due','payment_mode','payment_mode_supplier')
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
                    for term in invoice_payment_terms['line_ids']:

                        key = frozendict({
                            'move_id': invoice.id,
                            'date_maturity': fields.Date.to_date(term.get('date')),
                            'discount_date': term.get('discount_date'),
                        })
                        # add the value of amount_timbre to keep th balance 
                        balance = term['company_amount']
                        amount_currency = term['foreign_amount']

                        if invoice.company_id.based_on == 'posted_invoices':
                            balance += invoice.amount_timbre - invoice.amount_timbre_supplier 
                            amount_currency += invoice.amount_timbre - invoice.amount_timbre_supplier

                        values = {
                            'balance': balance ,
                            'amount_currency': amount_currency ,
                            'name': invoice.payment_reference or '',
                            'discount_amount_currency': invoice_payment_terms.get('discount_amount_currency') or 0.0,
                            'discount_balance': invoice_payment_terms.get('discount_balance') or 0.0,
                            'discount_date': invoice_payment_terms.get('discount_date'),
                        }
                        if key not in invoice.needed_terms:
                            invoice.needed_terms[key] = values
                        else:
                            invoice.needed_terms[key]['balance'] += values['balance']
                            invoice.needed_terms[key]['amount_currency'] += values['amount_currency']
                else:
                    balance2 = invoice.amount_total_signed 
                    amount_currency2 = invoice.amount_total_in_currency_signed


                    if invoice.company_id.based_on == 'posted_invoices':
                        balance2 += invoice.amount_timbre -  invoice.amount_timbre_supplier
                        amount_currency2 += invoice.amount_timbre -  invoice.amount_timbre_supplier

                    # add the value of amount_timbre to keep th balance 
                    invoice.needed_terms[frozendict({
                        'move_id': invoice.id,
                        'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
                        'discount_date': False,
                        'discount_percentage': 0
                    })] = {
                        'balance': balance2,
                        'amount_currency': amount_currency2 ,
                        'name': invoice.payment_reference or '',
                    }
    
   
    # override the original function

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
        'amount_timbre',
        'amount_timbre_supplier')
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

            move.total_timbre = move.amount_total + move.amount_timbre if move.amount_timbre else 0.0
            move.amount_with_timbre_supplier = move.amount_total + move.amount_timbre_supplier 

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
            timbre_supplier_filter = lambda m: (m.payment_mode_supplier.finn_mode_type == 'cash' and m.company_id.based_on == "posted_invoices" and m.move_type == "in_invoice")
    
            tax_container = {'records': container['records'].filtered(tax_filter)}
            invoice_container = {'records': container['records'].filtered(invoice_filter)}
            misc_container = {'records': container['records'].filtered(misc_filter)}

            # timbre_container
            timbre_container = {'records': container['records'].filtered(timbre_filter)}
            timbre_supplier_container = {'records': container['records'].filtered(timbre_supplier_filter)}

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

                # This will create/edit the line of timbre supplier
                stack.enter_context(self._sync_dynamic_line(
                    existing_key_fname='timbre_supplier_key',
                    needed_vals_fname='needed_timbre_supplier',
                    needed_dirty_fname='needed_timbre_supplier_dirty',
                    line_type='timbre',
                    container=timbre_supplier_container,
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
                timbre_supplier_container['records'] = container['records'].filtered(timbre_supplier_filter)


            # Delete the tax lines if the journal entry is not in "auto tax mode" anymore
            for move in container['records']:
                if move.move_type == 'entry' and not move.line_ids.tax_ids:
                    move.line_ids.filtered(
                        lambda l: l.display_type == 'tax'
                    ).with_context(dynamic_unlink=True).unlink()

               
                # Delete timbre line 
                if move.payment_mode.finn_mode_type != 'cash' or move.amount_timbre == 0 or move.line_ids.filtered(lambda l: l.display_type == 'timbre' and l.balance != -1* move.amount_timbre):
                    
                    if move.move_type == "out_invoice":

                        move.line_ids.filtered(
                            lambda l: l.display_type == 'timbre' and l.balance != -1* move.amount_timbre or l.balance == 0
                        ).with_context(dynamic_unlink=True).unlink()

                # Delete timbre supplier line 
                if move.payment_mode_supplier.finn_mode_type != 'cash' or move.amount_timbre_supplier == 0 or move.line_ids.filtered(lambda l: l.display_type == 'timbre' and l.balance != move.amount_timbre_supplier):
                    if move.move_type == "in_invoice":

                        move.line_ids.filtered(
                            lambda l: l.display_type == 'timbre' and l.balance != 1* move.amount_timbre_supplier or l.balance == 0
                        ).with_context(dynamic_unlink=True).unlink()




class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    timbre_supplier_key = fields.Binary(compute='_compute_timbre_supplier_key')

    # this will verify if the line timbre exist or not
    @api.depends('date_maturity')
    def _compute_timbre_supplier_key(self):

        for line in self:
            if line.display_type == 'timbre' and line.company_id.based_on == "posted_invoices" :
                account_timbre_id  = self.company_id.purchase_offset_account 
                line.timbre_supplier_key = frozendict({
                    'account_id': line.account_id.id,
                    'move_id': line.move_id.id,
                    'display_type': 'timbre',
   
                })
            else:
                line.timbre_supplier_key = False
       

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
            # if it's a timbre line don't add it to the tax compute
            elif line.display_type in ['timbre'] :
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

