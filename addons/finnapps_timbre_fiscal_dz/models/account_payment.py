# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging as log


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    based_on_related = fields.Selection(string='Based', related="company_id.based_on")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)



        # ajout droit de timbre
        for payment in self:
            if payment.use_timbre and line_vals_list:
                # Liquidity line. (ligne qui n utilise pas le compte client de l'invoice)
                payment_line_dict = line_vals_list[0]
                # payment_line_dict = payment_line[2]
                # ajout droit timbre au montant

                if payment_line_dict['debit']:
                    payment_line_dict['debit'] += payment.droit_timbre if payment_line_dict['debit'] > 0.0 else -1 * payment.droit_timbre
                elif payment_line_dict['credit']:
                    payment_line_dict['credit'] += payment.droit_timbre if payment_line_dict['credit'] > 0.0 else -1 * payment.droit_timbre

                if payment_line_dict['amount_currency']:
                    payment_line_dict['amount_currency'] = payment_line_dict['debit'] if payment_line_dict['debit'] else -1 * payment_line_dict['credit']

                company_currency = payment.company_id.currency_id
                if payment.currency_id == company_currency:
                    # Single-currency.
                    currency_id = payment.currency_id.id
                    # amount_currency_timbre = 0
                else:
                    # Multi-currencies.

                    # amount_currency_timbre = payment.currency_id._convert(
                    #     payment.droit_timbre,
                    #     company_currency,
                    #     payment.company_id,
                    #     payment.date)
                    currency_id = payment.currency_id.id

                account_timbre_id = self.company_id.sale_timbre
                if not account_timbre_id:
                    raise UserError(_('Les comptes pour les timbres ne sont pas configuré, veuillez remplir les comptes.'))

                #pour les deux :
                #      payment.partner_type in ['customer', 'supplier']
                for_credit = True if payment.payment_type == 'inbound' else False
                for_debit  = True if payment.payment_type == 'outbound'else False

                if payment.use_timbre and payment.droit_timbre > 0:

                    has_timbre_line = False

                    for line in line_vals_list:
                        if account_timbre_id.id == line['account_id'] :
                            line.update({
                                    'amount_currency': payment.droit_timbre if for_debit else -1 * payment.droit_timbre ,
                                    'debit': payment.droit_timbre if for_debit else 0.0,
                                    'credit': payment.droit_timbre if for_credit else 0.0,

                                    })
                            has_timbre_line = True

                    if not has_timbre_line:
                        line_vals_list.append({
                            'name': 'Droit de timbre',
                            'amount_currency': payment.droit_timbre if for_debit else -1 * payment.droit_timbre ,
                            'currency_id': currency_id,
                            'debit': payment.droit_timbre if for_debit else 0.0,
                            'credit': payment.droit_timbre if for_credit else 0.0,
                            'date_maturity': payment.date,
                            'partner_id': payment.partner_id.id,
                            'account_id': account_timbre_id.id,
                            # 'payment_id': payment.id,
                        })

        return line_vals_list


    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()
        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:

            if line.account_id in self._get_valid_liquidity_accounts():
                liquidity_lines += line
            #ajouter ligne de timbre au writeoff_lines
            elif line.account_id == line.company_id.sale_timbre :
                writeoff_lines += line
            elif line.account_id.account_type in ('asset_receivable', 'liability_payable') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            else:
                writeoff_lines += line


        return liquidity_lines, counterpart_lines, writeoff_lines




    def _synchronize_to_moves(self, changed_fields):
        # Vérification s'il y a lieu de synchroniser la pièece comptable
        if self._context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id',
            )):

            return

        # Récupération des lignes de la pièce comptable du paiements

        for pay in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Dans le cas ou le timbre est utilisé
            if self.use_timbre:

                pay.droit_timbre = int(self.company_id._timbre(pay.amount))


                # Mise à jour de la nouvelle valeur du droit de timbre en fonction du type du paiement
                write_off_line_vals = []
                if writeoff_lines:

                    write_off_line_vals.append({
                        'name': writeoff_lines[0].name,
                        'account_id': writeoff_lines[0].account_id.id,
                        'partner_id': writeoff_lines[0].partner_id.id,
                        'currency_id': writeoff_lines[0].currency_id.id,
                        'amount_currency': sum(writeoff_lines.mapped('amount_currency')) + pay.droit_timbre,
                        'balance': sum(writeoff_lines.mapped('balance')),
                    })

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

                if pay.payment_type == 'inbound':


                    line_vals_list[1]['amount_currency'] = - pay.amount
                    line_vals_list[1]['credit'] = pay.amount
                    if pay.payment_type == 'outbound':
                        raise UserError(_('Vous ne pouvez pas changer le type de paiment.'))


                if pay.payment_type == 'outbound':

                    line_vals_list[1]['amount_currency'] = pay.amount
                    line_vals_list[1]['debit'] = pay.amount

                    if pay.payment_type == 'outbound':
                        raise UserError(_('Vous ne pouvez pas changer le type de paiment.'))

                line_ids_commands = [
                                     (1, liquidity_lines.id, line_vals_list[0]),
                                     (1, counterpart_lines.id, line_vals_list[1]),
                                     ]

                ##############################################################################""
                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))


                if pay.droit_timbre != 0.0:
                    line_ids_commands.append((0, 0, line_vals_list[2]))

                self.move_id.write({
                                    'partner_id': pay.partner_id.id,
                                    'currency_id': pay.currency_id.id,
                                    'partner_bank_id': pay.partner_bank_id.id,
                                    'line_ids': line_ids_commands,
        
                                })
                
                return

        # Dans le cas ou l'ecriture du timbre doit être supprimer
        for writeoff_line in writeoff_lines:
            if writeoff_line.name == "Droit de timbre":

                timbre = pay.droit_timbre

                # Mise à jour de la nouvelle valeur du droit de timbre en fonction du type du paiement
                write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

                if pay.payment_type == 'inbound':

                    line_vals_list[1]['amount_currency'] = - pay.amount + timbre
                    line_vals_list[1]['credit'] = pay.amount - timbre
                    line_vals_list[0]['amount_currency'] = pay.amount - timbre
                    line_vals_list[0]['debit'] = pay.amount - timbre


                if pay.payment_type == 'outbound':

                    line_vals_list[1]['amount_currency'] = - pay.amount + timbre
                    line_vals_list[1]['credit'] = pay.amount - timbre



                    line_vals_list[0]['amount_currency'] = pay.amount - timbre
                    line_vals_list[0]['debit'] = pay.amount - timbre


                line_ids_commands = [
                                 (0, 0, line_vals_list[0]),
                                 (1, counterpart_lines.id, line_vals_list[1]),
                                 ]

                for line in writeoff_lines:
                    line_ids_commands.append((2,line.id))
                self.move_id.write({
                                'partner_id': pay.partner_id.id,
                                'currency_id': pay.currency_id.id,
                                'partner_bank_id': pay.partner_bank_id.id,
                                'line_ids': line_ids_commands,
                            })

                return

        res = super(AccountPayment, self)._synchronize_to_moves(changed_fields)

    @api.depends('journal_id', 'is_internal_transfer', 'currency_id')
    def _visible_timbre(self):

        for payment in self:
            if payment.journal_id.type == 'cash' and payment.partner_type != "supplier" and payment.company_id.based_on == 'payment' \
            and not payment.is_internal_transfer  and payment.company_id.currency_id == payment.currency_id:
                payment.use_timbre = True
            else :
                payment.use_timbre = False

    @api.depends('use_timbre')
    def _calcule_timbre(self):
        for payment in self:
            if payment.use_timbre:
                
                payment.droit_timbre = int(self.company_id._timbre(payment.amount))



    use_timbre = fields.Boolean(
        string='Utilise calcule timbre',
        compute='_visible_timbre',
        store=True,
    )

    droit_timbre = fields.Monetary(
        'Droit de timbre',
        compute='_calcule_timbre',
        store=True,
    )

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    based_on_related = fields.Selection(string='Based', related="company_id.based_on")
    """
    override wizard button_function to get the right value of "droit_timbre"
    """
    def _create_payment_vals_from_wizard(self ,batch_result):

        result = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)

        result['droit_timbre']=self.droit_timbre
        return result




    @api.depends('journal_id')
    def _visible_timbre(self):
        for payment in self:
            payment.use_timbre = True if payment.journal_id.type == 'cash' and payment.partner_type != "supplier"  and payment.company_id.based_on == 'payment' else False

    @api.depends('journal_id', 'amount')
    def _calcule_timbre(self):
       
        for payment in self:

            # payment.use_timbre = True if payment.journal_id.type == 'cash' else False
            if payment.use_timbre:

                payment.droit_timbre = int(self.company_id._timbre(payment.amount))

                payment.montant_avec_timbre = payment.amount + payment.droit_timbre


    use_timbre = fields.Boolean(
        string='Utilise calcule timbre',
        compute='_visible_timbre',
        store=True,
    )

    droit_timbre = fields.Monetary(
        'Droit de timbre',
        compute='_calcule_timbre',
        store=True,
    )

    montant_avec_timbre = fields.Monetary(
        'Montant avec timbre',
        compute='_calcule_timbre',
        store=True,
    )

class FinnPaymmentMode(models.Model):
    _name = 'finn.account.payment.mode'

    name = fields.Char(
        string="Nom",
        required=True
    )

    finn_mode_type = fields.Selection(
        [('cash', 'Especes'),
        ('bank', 'Banque'),
        ('libre','Libre')],
        string="Type"
    )
