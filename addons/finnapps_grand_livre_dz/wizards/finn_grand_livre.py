# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import ValidationError
import base64
import xlsxwriter
import logging as log

class FinnGrandLivre(models.TransientModel):
    _name = "finn.grand.livre"

    exercice_id = fields.Many2one(
        'finn.exercice',
        string='Exercice'
    )

    gl_tiers = fields.Boolean(
        string="Est un grand livre tiers"
        )

    filtrer_par_ecriture = fields.Selection(
        string='Filtre par écriture',
        selection=[
            ('no_reconciled', 'Écritures non lettrées'),
            ('all', 'Écritures lettrées et non lettrées'),
        ]
    )

    filtre_par_temps = fields.Selection(
        string='Filtrer par',
        selection=[
            ('rien', 'Pas de filtre'),
            ('date', 'Date'),
            ('periode', 'Période'),
        ],
        default='rien'
    )

    date_debut = fields.Date(
        string='Date de début'
    )

    date_fin = fields.Date(
        string='Date de fin'
    )

    periode_debut = fields.Many2one(
        comodel_name='finn.periode',
        string='Période de début'
    )

    periode_fin = fields.Many2one(
        comodel_name='finn.periode',
        string='Période de fin'
    )

    filtre_par_compte = fields.Selection(
        string='Filtrer par',
        selection=[
            ('rien', 'Pas de filtre'),
            ('classes_chapitres', 'Classes/Chapitres'),
            ('comptes', 'Comptes'),
        ],
        default='rien'
    )

    group_ids = fields.Many2many(
        comodel_name='account.group',
        string='Classes/Chapitres'
    )

    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Comptes'
    )



    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journaux'
    )

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Partenaires'
    )

    avec_devise = fields.Boolean(
        string='Avec devise'
    )

    centralisation_active = fields.Boolean(
        string='Centralisation activée'
    )

    binary_file = fields.Binary()
    
    file_name = fields.Char(
        default="Grand_livre_des_comptes.xlsx",
    )


    @api.onchange('gl_tiers')
    def onchange_account_ids(self):
        for record in self:
            account_receveible_payable = self.env['account.account'].search([('account_type','in',['liability_payable','asset_receivable'])])
            if record.gl_tiers == True:
                record.account_ids = account_receveible_payable.ids

    # recuperer date debut et fin selon
    # le filtre selectionnée
    def _get_date(self):
        if self.filtre_par_temps == 'date':
            date_from = self.date_debut
            date_to = self.date_fin
        elif self.filtre_par_temps == 'periode':
            date_from = self.periode_debut.date_from
            date_to = self.periode_fin.date_to
        else:
            date_from = self.exercice_id.date_from
            date_to = self.exercice_id.date_to

        return date_from, date_to

    # recuperer tous les comptes lié au group_id
    # et les fils du group_id et hierarchie des tous les fils
    def get_accounts_of_group(self, account_ids, group_id):
        for ai_id in group_id.account_ids.ids:
            account_ids.add(ai_id)
        # account_ids += group_id.account_ids.ids
        if not group_id.group_ids:
            return

        for gi in group_id.group_ids:
            self.get_accounts_of_group(account_ids, gi)

        return account_ids

    # recuperer toutes l'arboressence qui existe
    # entre classes <=> chapitres <=> comptes
    # selon les groupes selectionnée dans le filtre
    def get_accounts_of_groups(self):
        
        account_ids = self.env['account.account']
        for group_id in self.group_ids:
            ai_ids = self.get_accounts_of_group(set(), group_id)
            account_ids += self.env['account.account'].browse(ai_ids)
        return account_ids

    # recuperer les comptes a utilisé
    # lors de la recuperation des ecritures comptables
    def get_account_ids(self):
        if self.filtre_par_compte == 'comptes' and self.account_ids:
            return self.account_ids
        elif self.filtre_par_compte == 'classes_chapitres' and self.group_ids:
            return self.get_accounts_of_groups()
        else:
            return False

    # regroupé chaque ecriture comptable du meme compte
    def aml_grouped_by_account(self, aml_ids):
        account_grouped = {}
        for aml_id in aml_ids:
            account_id = aml_id.account_id
            if account_id not in account_grouped:
                account_grouped[account_id] = [aml_id]
            else:
                account_grouped[account_id].append(aml_id)
        return account_grouped

    def check_period(self, date_from, date_to):
        if date_from > date_to:
            raise ValidationError('Interval de temp incorrect !')

    def get_lines(self):
        date_from, date_to = self._get_date()
        self.check_period(date_from, date_to)

        aml_domain = [('date', '>=', date_from),
                  ('date', '<=', date_to)]

        if self.filtrer_par_ecriture == 'no_reconciled':
            aml_domain.append(('full_reconcile_id', '=', False))

        if self.journal_ids:
            aml_domain.append(('journal_id', 'in', self.journal_ids.ids))

        if self.partner_ids:
            aml_domain.append(('partner_id', 'in', self.partner_ids.ids))

        account_ids = self.get_account_ids()
        if account_ids:
            aml_domain.append(('account_id', 'in', account_ids.ids))

        aml_ids = self.env['account.move.line'].search(aml_domain, order="account_id asc").\
                        filtered(lambda aml: aml.move_id.period_id.is_closing_date == False)

        account_grouped = self.aml_grouped_by_account(aml_ids)

        datas = {
            'exercice': self.exercice_id,
            'avec_devise': self.avec_devise,
            'centralisation_active': self.centralisation_active,
            'filtre_ecriture': self.filtrer_par_ecriture,
            'filtre_compte': self.filtre_par_compte,
            'filtre_temp': {
                'type': self.filtre_par_temps,
                'date_debut': self.date_debut,
                'date_fin': self.date_fin,
                'periode_debut': self.periode_debut,
                'periode_fin': self.periode_fin,
            },
            'lines': [(account_id, aml_ids) for account_id, aml_ids in account_grouped.items()], # est un dict: {account_obj(1): aml_obj(1, 2, ...), ...}
        }

        return datas

    def print_report_pdf(self):
        if self.periode_fin < self.periode_debut and self.date_fin < self.date_debut:
            raise ValidationError('Interval de temp incorrect !')
        return self.env.ref('finnapps_grand_livre_dz.action_grand_livre_report').report_action(self)

    def print_report_excel(self):
        if self.periode_fin < self.periode_debut and self.date_fin < self.date_debut:
            raise ValidationError('Interval de temp incorrect !')
        
        OFFSET = 0
        data = self.get_lines()

        HEADER_FILTRE = ['Exercice comptable', 'Filtre par période', 'Filtre par compte', 'Filtre par écriture', 'Solde à nouveau']
        HEADER_DATA = ['Date', 'Période', 'Écriture', 'Journal', 'Partenaire', 'Référence', 'Description', 'Débit', 'Crédit', 'Solde']

        file_name = str('/var/lib/odoo/Grand_livre_des_comptes.xlsx')
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet('GRAND LIVRE DES COMPTES')

        # Set up worksheet
        for i in range(0,11):
            worksheet.set_column(i, i, 30)

        format_header = workbook.add_format({'bold': True, 'bg_color':"#d3d3d3", 'border':True})

        format_bold_bg = workbook.add_format({'bold': True, 'bg_color':"#d3d3d3"})

        format_header_right = workbook.add_format({'bold': True, 'bg_color':"#d3d3d3", 'align':'right', 'border':True})

        format_header_center = workbook.add_format({'bold': True, 'bg_color':"#d3d3d3", 'align':'center', 'border':True})

        format_bold = workbook.add_format({'bold': True})

        format_money = workbook.add_format({'num_format': '0.00', 'align':'right', 'border':True})

        format_money_bg = workbook.add_format({'num_format': '0.00', 'bg_color':"#d3d3d3", 'align':'right'})

        format_date = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align':'left', 'border':True})

        cell_format_left = workbook.add_format({'align':'left', 'border':True})

        cell_format_center = workbook.add_format({'align':'center', 'border':True})

        # ajouter titre de document
        company_id = self.env.user.company_id
        worksheet.write(OFFSET,1,'GRAND LIVRE DES COMPTES - {} - {}'.format(company_id.name, company_id.currency_id.name), format_bold)

        OFFSET += 1
        # Fill Header des filtres
        for i, h in enumerate(HEADER_FILTRE):
            worksheet.write(OFFSET, i, h, format_header_center)

        OFFSET += 1
        # remplir tableau des filtres
        filtre_compte = {
            'rien':'/',
            'classes_chapitres':'Classes/Chapitres',
            'comptes':'Comptes'
        }
        filtre_ecriture = {
            'no_reconciled':'Écritures non lettrées',
            'all':'Écritures lettrées et non lettrées',
        }

        worksheet.write(OFFSET, 0, data['exercice'].name, cell_format_center)

        if data['filtre_temp']['type'] == 'date':
            worksheet.write(OFFSET, 1, 'Depuis : {} - {}'.format(data['filtre_temp']['date_debut'], data['filtre_temp']['date_fin']), cell_format_center)
        elif data['filtre_temp']['type'] == 'periode':
            worksheet.write(OFFSET, 1, 'Depuis : {} - {}'.format(data['filtre_temp']['periode_debut'].name, data['filtre_temp']['periode_fin'].name), cell_format_center)
        else:
            worksheet.write(OFFSET, 1, '/', cell_format_center)

        worksheet.write(OFFSET, 2, filtre_compte[data['filtre_compte']], cell_format_center)
        worksheet.write(OFFSET, 3, filtre_ecriture[data['filtre_ecriture']], cell_format_center)
        worksheet.write(OFFSET, 4, '/', cell_format_center)

        OFFSET += 2
        # remplir les écritures comptables pour chaque compte
        for line in data['lines']:
            # recupere compte et ces ecritures comptables
            account_id = line[0]
            move_line_ids = line[1]

            worksheet.write(OFFSET, 0, account_id.code + ' - ' + account_id.name, format_bold)

            OFFSET += 1
            # Fill Header des données
            for i, h in enumerate(HEADER_DATA):
                if h in ['Débit', 'Crédit', 'Solde']:
                    worksheet.write(OFFSET, i, h, format_header_right)
                else:
                    worksheet.write(OFFSET, i, h, format_header)

            if data['avec_devise']:
                worksheet.write(OFFSET, 10, 'Devise', format_header_center)

            OFFSET += 1
            # remplir tableau des données
            sum_debit = 0
            sum_credit = 0
            for move_line_id in move_line_ids:
                worksheet.write(OFFSET, 0, move_line_id.date, format_date)
                worksheet.write(OFFSET, 1, move_line_id.period_id.name, cell_format_left)
                worksheet.write(OFFSET, 2, move_line_id.move_id.name, cell_format_left)

                if move_line_id.journal_id.code:
                    worksheet.write(OFFSET, 3, move_line_id.journal_id.code, cell_format_left)
                else:
                    worksheet.write(OFFSET, 3, '', cell_format_left)

                if move_line_id.partner_id.name:
                    worksheet.write(OFFSET, 4, move_line_id.partner_id.name, cell_format_left)
                else:
                    worksheet.write(OFFSET, 4, '', cell_format_left)

                if move_line_id.ref:
                    worksheet.write(OFFSET, 5, move_line_id.ref, cell_format_left)
                else:
                    worksheet.write(OFFSET, 5, '', cell_format_left)

                if move_line_id.name:
                    worksheet.write(OFFSET, 6, move_line_id.name, cell_format_left)
                else:
                    worksheet.write(OFFSET, 6, '', cell_format_left)

                worksheet.write(OFFSET, 7, move_line_id.debit, format_money)
                worksheet.write(OFFSET, 8, move_line_id.credit, format_money)
                worksheet.write(OFFSET, 9, (move_line_id.debit - move_line_id.credit), format_money)

                sum_debit += move_line_id.debit
                sum_credit += move_line_id.credit

                if data['avec_devise']:
                    if move_line_id.currency_id.name:
                        worksheet.write(OFFSET, 10, move_line_id.currency_id.name, cell_format_center)
                    else:
                        worksheet.write(OFFSET, 10, '', cell_format_center)

                OFFSET += 1

            # ajout ligne de solde cumulé
            worksheet.write(OFFSET, 0, account_id.code + ' - ' + account_id.name, format_bold_bg)
            worksheet.write(OFFSET, 1, '', format_bold_bg)
            worksheet.write(OFFSET, 2, '', format_bold_bg)
            worksheet.write(OFFSET, 3, '', format_bold_bg)
            worksheet.write(OFFSET, 4, '', format_bold_bg)
            worksheet.write(OFFSET, 5, '', format_bold_bg)
            worksheet.write(OFFSET, 6, 'Solde cumulé', format_bold_bg)
            worksheet.write(OFFSET, 7, sum_debit, format_money_bg)
            worksheet.write(OFFSET, 8, sum_credit, format_money_bg)
            worksheet.write(OFFSET, 9, (sum_debit - sum_credit), format_money_bg)

            if data['avec_devise']:
                worksheet.write(OFFSET, 10, '', format_bold_bg)

            OFFSET += 2

        workbook.close()

        with open(file_name, "rb") as f:
            self.binary_file = base64.b64encode(f.read())

        attachment_id = self.env['ir.attachment'].create({
            'name': 'Grand_livre_des_comptes.xlsx',
            'store_fname': 'Grand_livre_des_comptes.xlsx',
            'datas': self.binary_file
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id,),
            'target': 'new',
        }
#add 2 fields to account.group model because its missing in l10n_dz c14
class AccountGroup(models.Model):
    _inherit = 'account.group'

    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='group_id',
        string='Comptes liés'
    )

    group_ids = fields.One2many(
        comodel_name='account.group',
        inverse_name='parent_id',
        string='Groupes liés'
    )
