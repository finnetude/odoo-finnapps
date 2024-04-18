# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnLettrerEcriture(models.TransientModel):
    _name = 'finn.lettrer.ecriture'

    ecriture_to_close_id = fields.Many2one(
        'account.move',
        string="Ecriture de cloture",
        domain="[('period_id.is_opening_date','=',True),('period_id','!=',False)]"
    )

    ecriture_to_open_id = fields.Many2one(
        'account.move',
        string="Ecriture d'ouverture",
        domain="[('period_id.is_closing_date','=',True),('period_id','!=',False)]"
    )

    def finn_lettrer_ecriture(self):
        # regrouper les 'account.move.line' par compte puis les lettrées
        move_line_ids = self.env['account.move.line']
        if self.ecriture_to_open_id:
            move_line_ids += self.ecriture_to_open_id.line_ids
        if self.ecriture_to_close_id:
            move_line_ids += self.ecriture_to_close_id.line_ids

        move_line_by_account = {}
        for move_line_id in move_line_ids:
            account_id = move_line_id.account_id
            if account_id in move_line_by_account:
                move_line_by_account[account_id] += move_line_id
            else:
                move_line_by_account[account_id] = move_line_id

        for account_id, move_line_ids in move_line_by_account.items():

            debit_moves = move_line_ids.filtered(lambda r: r.debit != 0 or r.amount_currency > 0)
            credit_moves = move_line_ids.filtered(lambda r: r.credit != 0 or r.amount_currency < 0)
            debit_moves = debit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
            credit_moves = credit_moves.sorted(key=lambda a: (a.date_maturity or a.date, a.currency_id))
            #self.env['account.move.line']._reconcile_lines(debit_moves, credit_moves, 'amount_residual')
            (debit_moves + credit_moves).reconcile()


        self.ecriture_to_close_id.period_id.exercice_id.state = 'close'






