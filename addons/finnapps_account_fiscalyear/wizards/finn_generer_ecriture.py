# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnGenererEcriture(models.TransientModel):
    _name = 'finn.generer.ecriture'

    exercice_to_close_id = fields.Many2one(
        'finn.exercice',
        string='Exercice à fermer'
    )

    exercice_to_open_id = fields.Many2one(
        'finn.exercice',
        string='Nouvel exercice'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Journal d'ouverture"
    )

    journal_to_close_id = fields.Many2one(
        'account.journal',
        string="Journal de clôture"
    )

    description = fields.Char(
        string='Description des nouvelles écritures',
        default="Écriture de fin d'exercice"
    )

    def finn_set_move_line_vals(self, opening_move_line_vals_line, opening_move_id,
                                 closing_move_line_vals_line, closing_move_id,
                                 solde):
        if opening_move_id:
            opening_move_line_vals_line['debit'] = 0
            opening_move_line_vals_line['credit'] = 0
        if closing_move_id:
            closing_move_line_vals_line['debit'] = 0
            closing_move_line_vals_line['credit'] = 0

        if solde > 0:
            if opening_move_id:
                opening_move_line_vals_line['debit'] = solde
            if closing_move_id:
                closing_move_line_vals_line['credit'] = solde
        elif solde < 0:
            if opening_move_id:
                opening_move_line_vals_line['credit'] = solde * (-1)
            if closing_move_id:
                closing_move_line_vals_line['debit'] = solde * (-1)

    def finn_move_line_to_create(self, opening_move_line_vals_line, opening_move_id,
                                  closing_move_line_vals_line, closing_move_id):
        move_line_vals_list = []
        if opening_move_id:
            move_line_vals_list.append(opening_move_line_vals_line)
        if closing_move_id:
            move_line_vals_list.append(closing_move_line_vals_line)
        return move_line_vals_list

    def finn_get_debit_credit_solde(self, move_line_ids):
        sum_credit = sum(move_line_ids.mapped('credit'))
        sum_debit  = sum(move_line_ids.mapped('debit'))
        solde = sum_debit - sum_credit
        return sum_debit, sum_credit, solde

    def finn_get_account_ids(self, classes, user_type=[], include_user_type=None):
        account_ids = self.env['account.account'].search([]).filtered(lambda x: x.code[0] in classes)
        if user_type:
            if include_user_type == True:
                account_ids = account_ids.filtered(lambda x: x.account_type in user_type)
            elif include_user_type == False:
                account_ids = account_ids.filtered(lambda x: x.account_type not in user_type)
        return account_ids

    def finn_get_move_line_ids(self, account_ids, exercice_id):
        return self.env['account.move.line'].search([('account_id','in',account_ids.ids),
                                                     ('period_id','in',exercice_id.period_ids.ids)
                                                         ])

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

    def finn_generer_ecriture(self):
        account_move_obj = self.env['account.move']
        move_line_vals_list = []
        overwrite_opening_move = overwrite_closing_move = True

        # verifier si toutes les périodes de 'Exercice à fermer' sont fermées
        if 'open' in self.exercice_to_close_id.period_ids.mapped('state'):
            raise ValidationError("L'une des périodes de cette exercice ne pas fermée")

        opening_period_id = self.env['finn.periode'].search(['&',('exercice_id','=',self.exercice_to_open_id.id),
                                                            ('is_opening_date','=',True)])
        closing_period_id = self.env['finn.periode'].search(['&',('exercice_id','=',self.exercice_to_close_id.id),
                                                            ('is_closing_date','=',True)])
        # supprimer les deux 'account.move' de 'Nouvel exercice'
        # et 'Exercice à fermer', si elles sont déjà crées
        opening_old_move_id = account_move_obj.search(['&',('period_id','=',opening_period_id.id),
                                                           ('company_id','=',self.env.company.id)])
        closing_old_move_id = account_move_obj.search(['&',('period_id','=',closing_period_id.id),
                                                           ('company_id','=',self.env.company.id)])

        if opening_old_move_id.state == 'posted' or closing_old_move_id.state == 'posted':
            raise ValidationError('Les pièces sont validées, il est plus possible de lancer le processus de fermeture d’exercice')

        move_line_ids = []

        if opening_old_move_id.state != 'posted':
            move_line_ids += opening_old_move_id.line_ids.ids

        if closing_old_move_id.state != 'posted':
            move_line_ids += closing_old_move_id.line_ids.ids

        wizard_unreconcile = self.env['account.unreconcile'].with_context(active_ids=move_line_ids).create({})
        wizard_unreconcile.trans_unrec()

        if opening_old_move_id.state != 'posted':
            opening_old_move_id.with_context(force_delete=True).unlink()
        else:
            overwrite_opening_move = False

        if closing_old_move_id.state != 'posted':
            closing_old_move_id.with_context(force_delete=True).unlink()
        else:
            overwrite_closing_move = False

        # creer 'account.move' pour nouvel exercice
        if not opening_period_id:
            raise ValidationError("Nouvel exercice n'a pas une période d'ouverture")

        opening_move_id = False

        if overwrite_opening_move:
            opening_move_id = account_move_obj.create({
                'name': "Pièce d'ouverture " + self.exercice_to_open_id.name,
                'ref': self.description,
                'date': opening_period_id.date_from,
                'journal_id': self.journal_id.id,
            })

        # creer 'account.move' pour exercice à fermer
        if not closing_period_id:
            raise ValidationError("Exercice à fermer n'a pas une période de clôture")

        closing_move_id = False
        if overwrite_closing_move:
            closing_move_id = account_move_obj.create({
                'name': "Pièce de clôture " + self.exercice_to_close_id.name,
                'ref': self.description,
                'date': closing_period_id.date_from,
                'journal_id': self.journal_to_close_id.id,
            })

        # Récupérer les écritures avec des comptes qui appartient au classes (6 ou 7)
        # pour crée une écriture 'Écriture de centralisation' dans 'account.move'
        # de nouvel exercice et la dupliquer dans 'account.move' d'exercice à fermer
        # on inverse les valeurs des champs <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids(['6', '7'])
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_to_close_id)
        sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)

        
        account_benifice_id = self.env['account.account'].search([('account_type','=','equity_unaffected')], limit=1)


        if opening_move_id:
            opening_move_line_vals_line = {
                'name':'Écriture de centralisation',
                'journal_id':self.journal_id.id,
                'account_id':account_benifice_id.id,
                'date':opening_period_id.date_from,
                'move_id':opening_move_id.id,
            }

        if closing_move_id:
            closing_move_line_vals_line = {
                'name':'Écriture de centralisation',
                'journal_id':self.journal_to_close_id.id,
                'account_id':account_benifice_id.id,
                'date':closing_period_id.date_from,
                'move_id':closing_move_id.id,
            }

        self.finn_set_move_line_vals(opening_move_line_vals_line, opening_move_id,
                                closing_move_line_vals_line, closing_move_id,
                                solde)

        move_line_vals_list += self.finn_move_line_to_create(
                                    opening_move_line_vals_line, opening_move_id,
                                    closing_move_line_vals_line, closing_move_id)

        # Récupérer les écritures avec des comptes qui appartient au classes entre 1 et 5
        # et qui ne sont pas de type <Payable> ou <Recevable> pour crée une écriture
        # par compte dans 'account.move' de nouvel exercice et la dupliquer
        # dans 'account.move' d'exercice à fermer on inverse les valeurs des champs
        # <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], False)
        for account_id in account_ids:
            move_line_ids = self.finn_get_move_line_ids(account_id, self.exercice_to_close_id)
            if move_line_ids:
                sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
                if opening_move_id:
                    opening_move_line_vals_line = {
                        'name':'',
                        'journal_id':self.journal_id.id,
                        'account_id':account_id.id,
                        'date':opening_period_id.date_from,
                        'move_id':opening_move_id.id,
                    }

                if closing_move_id:
                    closing_move_line_vals_line = {
                        'name':'',
                        'journal_id':self.journal_to_close_id.id,
                        'account_id':account_id.id,
                        'date':closing_period_id.date_from,
                        'move_id':closing_move_id.id,
                    }

                self.finn_set_move_line_vals(opening_move_line_vals_line, opening_move_id,
                                        closing_move_line_vals_line, closing_move_id,
                                        solde)

                move_line_vals_list += self.finn_move_line_to_create(
                                            opening_move_line_vals_line, opening_move_id,
                                            closing_move_line_vals_line, closing_move_id)

        # Récupérer les écritures avec des comptes qui appartient au cloasses entre 1 et 5
        # et qui sont de type <Payable> ou <Recevable> pour crée une écriture
        # par (compte, partenaire) dans 'account.move' de nouvel exercice et la dupliquer
        # dans 'account.move' d'exercice à fermer on inverse les valeurs des champs
        # <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], True)
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_to_close_id)
        move_line_account_partner_ids = self.finn_get_grouped_move_lines_by_account_partner(move_line_ids)

        for account_partner, move_line_ids in move_line_account_partner_ids.items():
            account_id = account_partner[0]
            partner_id = account_partner[1]
            sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
            if opening_move_id:
                opening_move_line_vals_line = {
                    'name':'',
                    'journal_id':self.journal_id.id,
                    'account_id':account_id.id,
                    'partner_id':partner_id.id,
                    'date':opening_period_id.date_from,
                    'move_id':opening_move_id.id,
                }

            if closing_move_id:
                closing_move_line_vals_line = {
                    'name':'',
                    'journal_id':self.journal_to_close_id.id,
                    'account_id':account_id.id,
                    'partner_id':partner_id.id,
                    'date':closing_period_id.date_from,
                    'move_id':closing_move_id.id,
                }

            self.finn_set_move_line_vals(opening_move_line_vals_line, opening_move_id,
                                    closing_move_line_vals_line, closing_move_id,
                                    solde)

            move_line_vals_list += self.finn_move_line_to_create(
                                            opening_move_line_vals_line, opening_move_id,
                                            closing_move_line_vals_line, closing_move_id)

        self.env['account.move.line'].create(move_line_vals_list)
        # update period_id
        if opening_move_id:
            self._cr.execute("UPDATE account_move SET period_id = %s WHERE id = %s",
                                                    [opening_period_id.id, opening_move_id.id])
            self._cr.execute("UPDATE account_move_line SET period_id = %s WHERE move_id = %s",
                                                    [opening_period_id.id, opening_move_id.id])
        if closing_move_id:
            self._cr.execute("UPDATE account_move SET period_id = %s WHERE id = %s",
                                                    [closing_period_id.id, closing_move_id.id])
            self._cr.execute("UPDATE account_move_line SET period_id = %s WHERE move_id = %s",
                                                        [closing_period_id.id, closing_move_id.id])
        
        # fermer l'exercice
        self.exercice_to_close_id.state = 'close'


    def finn_test_generer_ecriture(self):
        account_move_obj = self.env['account.move']
        move_line_vals_list = []
        overwrite_opening_move = overwrite_closing_move = True

        # verifier si toutes les périodes de 'Exercice à fermer' sont fermées
        if 'open' in self.exercice_to_close_id.period_ids.mapped('state'):
            raise ValidationError("L'une des périodes de cette exercice ne pas fermée")

        opening_period_id = self.env['finn.periode'].search(['&',('exercice_id','=',self.exercice_to_open_id.id),
                                                            ('is_opening_date','=',True)])
        closing_period_id = self.env['finn.periode'].search(['&',('exercice_id','=',self.exercice_to_close_id.id),
                                                            ('is_closing_date','=',True)])
        # supprimer les deux 'account.move' de 'Nouvel exercice'
        # et 'Exercice à fermer', si elles sont déjà crées
        opening_old_move_id = account_move_obj.search(['&',('period_id','=',opening_period_id.id),
                                                           ('company_id','=',self.env.company.id)])
        closing_old_move_id = account_move_obj.search(['&',('period_id','=',closing_period_id.id),
                                                           ('company_id','=',self.env.company.id)])

        if opening_old_move_id.state == 'posted' or closing_old_move_id.state == 'posted':
            raise ValidationError('Les pièces sont validées, il est plus possible de lancer le processus de fermeture d’exercice')

        move_line_ids = []

        if opening_old_move_id.state != 'posted':
            move_line_ids += opening_old_move_id.line_ids.ids

        if closing_old_move_id.state != 'posted':
            move_line_ids += closing_old_move_id.line_ids.ids

        wizard_unreconcile = self.env['account.unreconcile'].with_context(active_ids=move_line_ids).create({})
        wizard_unreconcile.trans_unrec()

        if opening_old_move_id.state != 'posted':
            opening_old_move_id.with_context(force_delete=True).unlink()
        else:
            overwrite_opening_move = False

        if closing_old_move_id.state != 'posted':
            closing_old_move_id.with_context(force_delete=True).unlink()
        else:
            overwrite_closing_move = False

        # creer 'account.move' pour nouvel exercice
        if not opening_period_id:
            raise ValidationError("Nouvel exercice n'a pas une période d'ouverture")

        # creer 'account.move' pour exercice à fermer
        if not closing_period_id:
            raise ValidationError("Exercice à fermer n'a pas une période de clôture")
        
        balance_totale = 0

        # Récupérer les écritures avec des comptes qui appartient au classes (6 ou 7)
        # pour crée une écriture 'Écriture de centralisation' dans 'account.move'
        # de nouvel exercice et la dupliquer dans 'account.move' d'exercice à fermer
        # on inverse les valeurs des champs <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids(['6', '7'])
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_to_close_id)
        sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
        
        account_benifice_id = self.env['account.account'].search([('account_type','=','equity_unaffected')], limit=1)

        journal_txt = "Récupération du solde de la classe 6 et 7 sur le compte de bénéfice\n"
        journal_txt += 'Le solde total du compte {} est de {}\n'.format(account_benifice_id.code, round(solde, 2))
        balance_totale += solde

        # Récupérer les écritures avec des comptes qui appartient au classes entre 1 et 5
        # et qui ne sont pas de type <Payable> ou <Recevable> pour crée une écriture
        # par compte dans 'account.move' de nouvel exercice et la dupliquer
        # dans 'account.move' d'exercice à fermer on inverse les valeurs des champs
        # <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], False)
        journal_txt += "\nRécupération du solde de la classe 1 à 5 pour les comptes qui ne sont pas de type <Payable>\n"
        for account_id in account_ids:
            move_line_ids = self.finn_get_move_line_ids(account_id, self.exercice_to_close_id)
            if move_line_ids:
                sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
                journal_txt += 'Le solde total du compte {} est de {}\n'.format(account_id.code, round(solde, 2))
                balance_totale += solde

        # Récupérer les écritures avec des comptes qui appartient au cloasses entre 1 et 5
        # et qui sont de type <Payable> ou <Recevable> pour crée une écriture
        # par (compte, partenaire) dans 'account.move' de nouvel exercice et la dupliquer
        # dans 'account.move' d'exercice à fermer on inverse les valeurs des champs
        # <Crédit> et <Débit> pour cette copie
        account_ids = self.finn_get_account_ids([str(i) for i in range(1, 6)], ['payable','receivable'], True)
        move_line_ids = self.finn_get_move_line_ids(account_ids, self.exercice_to_close_id)
        move_line_account_partner_ids = self.finn_get_grouped_move_lines_by_account_partner(move_line_ids)

        journal_txt += "\nRécupération du solde de la classe 1 à 5 pour les comptes qui sont de type <Payable> ou <Recevable>\n"

        for account_partner, move_line_ids in move_line_account_partner_ids.items():
            account_id = account_partner[0]
            partner_id = account_partner[1]
            sum_debit, sum_credit, solde = self.finn_get_debit_credit_solde(move_line_ids)
            journal_txt += 'Le solde total du compte {} pour le partenaire {} est de {}\n'.format(
                account_id.code, 
                partner_id.name if partner_id else 'inconnu', 
                round(solde, 2))
            balance_totale += solde

        journal_txt += '\nLa balance total est de {}\n'.format(round(balance_totale, 2))

        raise ValidationError(journal_txt)


