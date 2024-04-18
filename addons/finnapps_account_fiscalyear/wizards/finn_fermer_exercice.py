# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnFermerExercice(models.TransientModel):
    _name = 'finn.fermer.exercice'

    exercice_id = fields.Many2one(
        'finn.exercice',
        string='Exercice à fermer'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Journal d'ouverture"
    )

    description = fields.Char(
        string='Description des nouvelles écritures',
        default="Écriture de fin d'exercice")

    def finn_get_debit_credit_solde(self, move_line_ids):
        sum_debit  = sum(move_line_ids.mapped('debit'))
        sum_credit = sum(move_line_ids.mapped('credit'))
        solde = sum_debit - sum_credit
        return sum_debit, sum_credit, solde

    def finn_set_closing_move_vals(self, closing_move_line_vals_line, solde):
        closing_move_line_vals_line['debit'] = 0
        closing_move_line_vals_line['credit'] = 0

        if solde > 0:
            closing_move_line_vals_line['credit'] = solde
        elif solde < 0:
            closing_move_line_vals_line['debit'] = solde * (-1)

    def finn_get_grouped_move_lines_by_account_partner(self, move_line_ids):
        move_line_account_partner_ids = {}

        for move_line_id in move_line_ids:
            account_id = move_line_id.account_id
            partner_id = move_line_id.partner_id

            if (account_id, partner_id) in move_line_account_partner_ids:
                move_line_account_partner_ids[(account_id, partner_id)] += move_line_id
            else:
                move_line_account_partner_ids[(account_id, partner_id)] = move_line_id

        return move_line_account_partner_ids

    def finn_get_account_ids(self, classes, user_type=[], include_user_type=None):
        account_ids = self.env['account.account'].search([]).filtered(lambda x: x.code[0] in classes)
        if user_type:
            if include_user_type == True:
                account_ids = account_ids.filtered(lambda x: x.account_type in user_type)
            elif include_user_type == False:
                account_ids = account_ids.filtered(lambda x: x.account_type not in user_type)
        return account_ids

    def finn_get_move_line_ids(self, account_ids, exercice_id, full_reconcile_id):
        return self.env['account.move.line'].search(['&',('account_id','in',account_ids.ids),
                                                     '&',('period_id','in',exercice_id.period_ids.ids),
                                                         ('full_reconcile_id','=',full_reconcile_id)])

    def finn_fermer_exercice(self):
        account_move_obj = self.env['account.move']
        move_line_vals_list = []
        # verifier si toutes les périodes de 'Exercice à fermer' sont fermées
        if 'open' in self.exercice_id.period_ids.mapped('state'):
            raise ValidationError("L'une des périodes de cette exercice ne pas fermée")

        closing_period_id = self.exercice_id.period_ids.filtered(lambda p: p.is_closing_date)
        # supprimer la piece de cloture de 'Exercice à fermer', si elle est déjà crée
        closing_old_move_id = account_move_obj.search(['&',('period_id','=',closing_period_id.id),
                                                           ('company_id','=',self.env.company.id)])
        if closing_old_move_id.state == 'posted':
            raise ValidationError('La pièce est validée, il est plus possible de lancer le processus de fermeture d’exercice')

        if closing_old_move_id:
            # annuler lettrage
            wizard_unreconcile = self.env['account.unreconcile'].with_context(active_ids=closing_old_move_id.line_ids.ids).create({})
            wizard_unreconcile.trans_unrec()
            # supprimer l'ancienne piece comptable de cloture
            closing_old_move_id.unlink()

        # creer la nouvelle piece comptable de cloture
        if not closing_period_id:
            raise ValidationError("Exercice à fermer n'a pas une période de clôture")

        closing_move_id = account_move_obj.create({
            'name': self.description,
            'ref': '',
            'date': closing_period_id.date_from,
            'journal_id': self.journal_id.id,
        })

        # Récupérer les écritures avec des comptes qui appartient au classes (6 ou 7)
        # pour crée une écriture 'Écriture de centralisation' dans la nouvelle piece comptable
        # de cloture d'exercice à fermer on inverse les valeurs des champs <Crédit> et <Débit>"
        account_ids = self.finn_get_account_ids(['6', '7'])
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_id, False)
        sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
        # xml_id = self.env.ref('account.data_unaffected_earnings').id
        account_benifice_id = self.env['account.account'].search([('account_type','=','equity_unaffected')], limit=1)

        closing_move_line_vals_line = {
            'name': 'Écriture de centralisation',
            'journal_id': self.journal_id.id,
            'account_id': account_benifice_id.id,
            'date': closing_period_id.date_from,
            'move_id': closing_move_id.id,
        }
        self.finn_set_closing_move_vals(closing_move_line_vals_line, solde)
        move_line_vals_list.append(closing_move_line_vals_line)

        # Récupérer les écritures avec des comptes qui appartient au classes entre 1 et 5
        # et qui ne sont pas de type <Payable> ou <Recevable> pour crée une écriture
        # par compte dans la nouvelle piece comptable de cloture d'exercice à fermer
        # on inverse les valeurs des champs <Crédit> et <Débit>
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], False)
        for account_id in account_ids:
            move_line_ids = self.finn_get_move_line_ids(account_id, self.exercice_id, False)
            if move_line_ids:
                sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
                closing_move_line_vals_line = {
                    'name': '',
                    'journal_id': self.journal_id.id,
                    'account_id': account_id.id,
                    'date': closing_period_id.date_from,
                    'move_id': closing_move_id.id,
                }
                self.finn_set_closing_move_vals(closing_move_line_vals_line, solde)
                move_line_vals_list.append(closing_move_line_vals_line)

        # Récupérer les écritures avec des comptes qu appartient au classes entre 1 et 5
        # et qui sont de type <Payable> ou <Recevable> pour crée une écriture
        # par (compte, partenaire) dans la nouvelle piece comptable d'exercice à fermer
        # on inverse les valeurs des champs <Crédit> et <Débit>
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], True)
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_id, False)
        move_line_account_partner_ids = self.finn_get_grouped_move_lines_by_account_partner(move_line_ids)
        for account_partner, move_line_ids in move_line_account_partner_ids.items():
            account_id = account_partner[0]
            partner_id = account_partner[1]
            sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
            closing_move_line_vals_line = {
                'name':'',
                'journal_id':self.journal_id.id,
                'account_id':account_id.id,
                'partner_id':partner_id.id,
                'date':closing_period_id.date_from,
                'move_id':closing_move_id.id,
            }
            self.finn_set_closing_move_vals(closing_move_line_vals_line, solde)
            move_line_vals_list.append(closing_move_line_vals_line)

        self.env['account.move.line'].create(move_line_vals_list)
        # update period_id
        self._cr.execute("UPDATE account_move SET period_id = %s WHERE id = %s",
                                                [closing_period_id.id, closing_move_id.id])
        self._cr.execute("UPDATE account_move_line SET period_id = %s WHERE move_id = %s",
                                                    [closing_period_id.id, closing_move_id.id])
        # fermer l'exercice
        self.exercice_id.state = 'close'

