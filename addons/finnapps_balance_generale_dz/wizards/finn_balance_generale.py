# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date , datetime
from odoo.exceptions import ValidationError
import logging as log

FILTRER_PAR_ECRITURE_SELECTION = [
            ('non_lettrees', 'Écritures non lettrées'),
            ('tous', 'Écritures lettrées et non lettrées'),
        ]

FILTRER_PAR_COMPTE_SELECTION = [
            ('tous','Tous'),
            ('avec_movement','Avec mouvements'),
            ('non_zero','Avec la balance qui n\'est pas égale à 0')
        ]

FILTRER_PAR_PIECE_SELECTION = [
            ('valide', 'Écritures validées'),
            ('tous', 'Écritures validées et brouillon'),
        ]

class FinnBalanceGenerale(models.TransientModel):
    _name = "finn.balance.generale"

    date_from = fields.Date(
        string='Date de début',
    )

    date_to = fields.Date(
        string='Date de fin',
    )

    period_from_id = fields.Many2one(
        'finn.periode', 
        string='Période de début',
    )
    
    period_to_id = fields.Many2one(
        'finn.periode', 
        string='Période de fin',
    )
    
    exercice_id = fields.Many2one(
        'finn.exercice', 
        string='Exercice',
    )
    
    filtrer_par_ecriture = fields.Selection(
        string='Filtre par mouvement',
        selection=FILTRER_PAR_ECRITURE_SELECTION,
    )

    filtrer_par_temps = fields.Selection(
        string='Filtrer par',
        selection=[
            ('rien', 'Pas de filtre'),
            ('date', 'Date'),
            ('periode', 'Période')],
        default='rien',
    )
    
    filtrer_par_compte = fields.Selection(
        string='Afficher les comptes',
        selection=FILTRER_PAR_COMPTE_SELECTION,
    )
    
    filtrer_par_piece = fields.Selection(
        string='Filtre par écriture',
        selection=FILTRER_PAR_PIECE_SELECTION,
    )

    bg_tiers = fields.Boolean(
        string="Est une balance générale tiers"
        )

    bg_clients = fields.Boolean(
        string="Est une balance âgée des clients"
        )

    bg_fournisseurs = fields.Boolean(
        string="Est une balance âgée des fournisseurs"
        )

    def imprimer_rapport(self):
        return self.env.ref('finnapps_balance_generale_dz.action_balance_generale_report').report_action(self)

    def get_data(self):
        date_from, date_to = self.get_date()
        self.verifier_periode(date_from, date_to)
        account_data = {}

        move_line_domain = [
            ('date','>=',date_from),
            ('date','<=',date_to),
            ('period_id.is_closing_date','=',False)
        ]

        if self.filtrer_par_ecriture == 'non_lettrees':
            move_line_domain.append(('full_reconcile_id','=',False))

        move_line_ids = self.env['account.move.line'].search(move_line_domain)

        # filtre par compte
        
        if self.filtrer_par_compte == 'avec_movement':
            account_data = self.get_account_data(move_line_ids, account_data_input=account_data)
        elif self.filtrer_par_compte == 'non_zero':
            account_to_delete = []
            account_data = self.get_account_data(move_line_ids, account_data_input=account_data)

            # recupere les comptes qui ont solde non zero
            for account_id, values in account_data.items():
                if values[4] == 0 and values[5] == 0:
                    account_to_delete.append(account_id)

            # supprimer les comptes qui ont solde non zero
            for account_id in account_to_delete:
                del account_data[account_id]
        else:
            account_ids = self.env['account.account'].search([])

            for account_id in account_ids:
                # initialisation
                account_data[account_id] = [0, 0 ,0, 0, 0, 0]

            account_data = self.get_account_data(move_line_ids, account_data_input=account_data)

        variable=self.sort_account_data(account_data)
        data = {
            'exercice_name':self.exercice_id.name,
            'periode_intervale':'Depuis : ' + str(date_from.strftime("%d-%m-%Y")) + ' à ' + str(date_to.strftime("%d-%m-%Y")),
            'filtrer_par_compte':dict(FILTRER_PAR_COMPTE_SELECTION)[self.filtrer_par_compte],
            'filtrer_par_ecriture':dict(FILTRER_PAR_ECRITURE_SELECTION)[self.filtrer_par_ecriture],
            'filtrer_par_piece':dict(FILTRER_PAR_PIECE_SELECTION)[self.filtrer_par_piece],
            'account_data':variable,
        }
        
        return data

    # recupere les valeurs de debit et credit pour : overture et periode
    # calculer les soldes
    def get_account_data(self, move_line_ids, account_data_input={}):
        account_data = account_data_input

        # pour chaque ecriture
        for move_line_id in move_line_ids:
            account_id = move_line_id.account_id
            debit = move_line_id.debit
            credit = move_line_id.credit

            if account_id in account_data:
                # faite la somme des debits et credits
                if self.filtrer_par_piece == 'valide':
                    if move_line_id.period_id.is_opening_date and move_line_id.move_id.state == 'posted':
                        account_data[account_id][0] += debit
                        account_data[account_id][1] += credit
                    elif move_line_id.move_id.state == 'posted':
                        account_data[account_id][2] += debit
                        account_data[account_id][3] += credit
                else:
                    if move_line_id.period_id.is_opening_date:
                        account_data[account_id][0] += debit
                        account_data[account_id][1] += credit
                    else:
                        account_data[account_id][2] += debit
                        account_data[account_id][3] += credit
            else:
                # initialisation
                if self.filtrer_par_piece == 'valide':
                    if move_line_id.period_id.is_opening_date and move_line_id.move_id.state == 'posted':
                        account_data[account_id] = [debit, credit, 0, 0, 0, 0]
                    elif move_line_id.move_id.state == 'posted':
                        account_data[account_id] = [0, 0, debit, credit, 0, 0]
                else:
                    if move_line_id.period_id.is_opening_date:
                        account_data[account_id] = [debit, credit, 0, 0, 0, 0]
                    else:
                        account_data[account_id] = [0, 0, debit, credit, 0, 0]

        # calculer solde pour chque compte
        for account_id, values in account_data.items():
            solde = (values[0] + values[2]) - (values[1] + values[3])
            if solde > 0:
                account_data[account_id][4] = solde
                account_data[account_id][5] = 0
            elif solde < 0:
                account_data[account_id][4] = 0
                account_data[account_id][5] = solde * (-1)
            else:
                account_data[account_id][4] = 0
                account_data[account_id][5] = 0
        return account_data

    # construire l'arborescence de plan des comptes
    def sort_account_data(self, account_data):
        account_group_obj = self.env['account.group']
        sorted_account_data = {}
        data_copy = {}

        # recupere groupe de niveau 1
        grp_1_ids = account_group_obj.search([('parent_id','=',False)])
        for grp_1_id in grp_1_ids:
            sorted_account_data[grp_1_id] = {}
            data_copy[grp_1_id] = {}

            # recupere groupe de niveau 2
            grp_2_ids = account_group_obj.search([('parent_id','=',grp_1_id.id)])
            for grp_2_id in grp_2_ids:
                sorted_account_data[grp_1_id][grp_2_id] = {}
                data_copy[grp_1_id][grp_2_id] = {}

                # recupere groupe de niveau 3
                grp_3_ids = account_group_obj.search([('parent_id','=',grp_2_id.id)])
                for grp_3_id in grp_3_ids:
                    sorted_account_data[grp_1_id][grp_2_id][grp_3_id] = {}
                    data_copy[grp_1_id][grp_2_id][grp_3_id] = {}

                    # recupere groupe de niveau 4
                    grp_4_ids = account_group_obj.search([('parent_id','=',grp_3_id.id)])
                    for grp_4_id in grp_4_ids:
                        sorted_account_data[grp_1_id][grp_2_id][grp_3_id][grp_4_id] = {}
                        data_copy[grp_1_id][grp_2_id][grp_3_id][grp_4_id] = {}




        # pour chaque compte
        for account_id, values in account_data.items():
            for grp_1_id, grp_2_dict in sorted_account_data.items():
                for grp_2_id, grp_3_dict in grp_2_dict.items():
                    # for grp_3_id, grp_4_dict in grp_3_dict.items():
                    #     for grp_4_id, grp_4_data in grp_4_dict.items():

                    # si le groupe de niveau 4 est un parent direct de compte
                    if account_id.group_id.id == grp_2_id.id:
                        sorted_account_data[grp_1_id][grp_2_id][account_id] = values
                        data_copy[grp_1_id][grp_2_id][account_id] = values

                    # si le groupe de niveau 4 est un parent indirect (parent 2) de compte
                    elif account_id.group_id.parent_id.id == grp_2_id.id:
                        parent_id = account_id.group_id.parent_id

                        # ajout groupe parent direct de compte sous le groupe de niveau 4
                        if not parent_id in grp_2_data:
                            sorted_account_data[grp_1_id][grp_2_id][parent_id] = {}
                            data_copy[grp_1_id][grp_2_id][parent_id] = {}

                        sorted_account_data[grp_1_id][grp_2_id][parent_id][account_id] = values
                        data_copy[grp_1_id][grp_2_id][grp_3_id][account_id] = values

                    # si le groupe de niveau 4 est un parent indirect (parent 3) de compte
                    elif account_id.group_id.parent_id.parent_id.id == grp_2_id.id:
                        parent_1_id = account_id.group_id.parent_id.parent_id
                        parent_2_id = account_id.group_id.parent_id

                        # ajout groupe parent indirect (parent 2) de compte sous le groupe de niveau 4
                        if not parent_1_id in grp_2_data:
                            sorted_account_data[grp_1_id][grp_2_id][parent_1_id] = {}
                            data_copy[grp_1_id][grp_2_id][parent_1_id] = {}

                        parent_2_data = sorted_account_data[grp_1_id][grp_2_id][parent_1_id]

                        # ajout groupe parent direct de compte sous le groupe de niveau 4 s'il existe pas
                        # apres ajouter le compte
                        if parent_2_id in parent_2_data:
                            sorted_account_data[grp_1_id][grp_2_id][parent_1_id][parent_2_id].append((account_id, values))
                            data_copy[grp_1_id][grp_2_id][grp_3_id][parent_2_id].append((account_id, values))
                        else:
                            sorted_account_data[grp_1_id][grp_2_id][parent_1_id][parent_2_id] = [(account_id, values)]
                            data_copy[grp_1_id][grp_2_id][parent_1_id][parent_2_id] = [(account_id, values)]
        
        var = self.delete_empty_nodes(sorted_account_data, data_copy)
        return var

    # supprimer tous les noeuds qu'ont pas de fils
    def delete_empty_nodes(self, data, data_copy):
        for grp_1_id, grp_2_dict in data_copy.items():
            for grp_2_id, grp_2_data in grp_2_dict.items():
                
                for key_1, values_1 in grp_2_data.items():
                    if isinstance(values_1, dict):
                        for key_2, values_2 in values_1.items():
                            # supprimer parent 6 si il est pas de fils
                            if not values_2:
                                del data[grp_1_id][grp_2_id][key_1][key_2]

                        # supprimer parent 5 si il est pas de fils
                        if not data[grp_1_id][grp_2_id][key_1]:
                            del data[grp_1_id][grp_2_id][key_1]


                # supprimer parent 2 si il est pas de fils
                if not data[grp_1_id][grp_2_id]:
                    del data[grp_1_id][grp_2_id]

            # supprimer parent 1 si il est pas de fils
            if not data[grp_1_id]:
                del data[grp_1_id]

        return data

    def verifier_periode(self, date_from, date_to):
        if date_from > date_to:
            raise ValidationError('Période incorrecte')

    # recuperer date debut et fin selon
    # le filtre selectionnée
    def get_date(self):
        if self.filtrer_par_temps == 'date':
            date_from = self.date_from
            date_to = self.date_to
        elif self.filtrer_par_temps == 'periode':
            date_from = self.period_from_id.date_from
            date_to = self.period_to_id.date_to
        else:
            date_from = self.exercice_id.date_from
            date_to = self.exercice_id.date_to

        return date_from, date_to

    def get_current_date(self):
        return date.today()
