# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
import collections

import logging as log

montan_du = 0
previous_solde = 0


class FinnImprimerRapport(models.TransientModel):

    _name = 'finn.imprimer.rapport'

    
    
    
    def default_partner(self):
        domain = self.env.context.get('default_domain_record')
        move_line = self.env['account.move.line'].search(domain)
        partner = move_line.mapped('partner_id')
        if len(partner) == 1:
            return partner[0]  
        else :
            return False   

    partner_id = fields.Many2one('res.partner',string="Partenaire")
    
    domain_record = fields.Char("Domain")

    print_type = fields.Selection(string="Type de documents" ,
        selection=[
            ('client','Solde d\'un client'),
            ('all','Solde de tous les clients')

        ],
        default="client"
    )

    add_message = fields.Boolean(
        default=False,
        string='Afficher ce message pour le client'
    )
    
   
    message = fields.Text(
        default="Madame, Monsieur,"+
                "\nD'après nos relevés, il semble que nous sommes encore en attente à ce jour de paiements de votre part, dont"+
                "\nles détails sont indiqués ci-dessous. Si ces sommes ont déjà été réglées, vous pouvez ignorer ce rappel. Dans le cas contraire,"+
                "\nnous vous remercions de bien vouloir nous faire parvenir votre règlement. Si vous avez d'autres questions concernant votre"+
                "\ncompte, vous pouvez nous contacter directement. En vous remerciant par avance."
                "\nCordialement,",
    )
    body = fields.Char()
    is_error_message = fields.Boolean(default=False)

    bon_de_vente = fields.Selection(
        selection=[
            ('1','Uniquement ceux ouvertes'),
            ('2','Tous ceux de l\'année'),
            ('3','Tous ceux existants')
        ],
        default='1',
        string="Impression des documents de vente",
    )

    impression_bv = fields.Boolean(
        string="Imprimer les Bons de vente existants",
        default=True,
    )

    move_ids = fields.Many2many('account.move', relation='mymodule_move_rel')

    solde_printed = fields.Boolean(default=False, store=True)

   
    def print_report_invoice(self):
        self.get_bon_ventes()
        return self.move_ids.sudo().action_invoice_print() if self.move_ids else False

    def print_report(self):
        self.solde_printed = True
        return self.env.ref('finnapps_solde_tiers.action_print_report_solde_tiers').report_action(self)

    def print_report_all(self):

        return self.env.ref('finnapps_solde_tiers.action_print_report_solde_tiers_all').report_action(self)


    def send_mail(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move.line'].browse(selected_ids)
        mail_template_id = self.env.ref('finnapps_solde_tiers.mail_template_solde_tiers')
        

        if self.partner_id.email:
            self.env['mail.template'].browse(mail_template_id.id).send_mail(self.id, force_send=True)

    
    def get_lines(self):

        global montan_du
        global previous_solde

        sum_debit_pour_montant = 0
        sum_credit_pour_montant = 0
        
        domain = [('account_type', 'in', ['asset_receivable' ,'liability_payable']),('move_id.state','=','posted') ]

        #domain = eval(self.domain_record)
            ### For report solde tiers  _____________________________

        if self.partner_id:
            list_dom = []
            for count, elem in enumerate(domain):
                if elem[0] == 'partner_id' and list_dom:
                    if list_dom[-1] == '|':
                        list_dom.pop()   
                if elem[0] != 'partner_id':
                    list_dom.append(elem)
            list_dom.append(['partner_id','=',self.partner_id.id])
        else :
            list_dom = domain

        lines = self.env['account.move.line'].search(list_dom, order = 'date asc')

        if not lines :
            return

        else:
            data = []
            grouped_dict = {}

            ########## previous solde ###################
            if not list_dom or not self.partner_id :
                previous_solde = 0
            else :
                order = "date desc ,id desc ,id"
                print("oooookey")
                result ,result_all = self.env['account.move.line'].compute_cumulated_balance(order, list_dom, limit=True)

                move_lines = self.env['account.move.line'].search([('id','=',list(result.keys())[0])],order="date asc ,id asc ,id")
                if move_lines.id in result_all:

                    cumulated_balance = result_all[move_lines.id]
                else:

                    cumulated_balance = result[move_lines.id]

                previous_solde = cumulated_balance - lines[0].balance


            for line in lines :
                
                if line.date_maturity:
                    move_date = line.date_maturity
                else:
                    move_date = line.date


                if line.partner_id.name in grouped_dict:
                    grouped_dict[line.partner_id.name].append([line.date, line.ref, line.name, line.date_maturity, line.debit - line.credit, line.residual])
                else:
                    grouped_dict[line.partner_id.name] = [[line.date, line.ref, line.name, line.date_maturity, line.balance,  line.residual]]

                # data.append([line.ref, line.date, line.date_maturity, line.name, line.debit, line.credit, line.debit-line.credit])
               


                if move_date <= self.get_date_today():
                    sum_debit_pour_montant += line.debit
                    sum_credit_pour_montant += line.credit

            montan_du = sum_debit_pour_montant - sum_credit_pour_montant + previous_solde
            montan_du = montan_du if montan_du >= 0 else 0


            return grouped_dict
        

        
    def get_lines_all(self):
        ### For report solde tiers ALL_____________________________

        domain = [('account_type', 'in', ['asset_receivable' ,'liability_payable']),('move_id.state','=','posted') ]

        lines = self.env['account.move.line'].search([('account_type', 'in', ['asset_receivable' ,'liability_payable']),('move_id.state','=','posted')],order = 'partner_id desc')

        lines_total = self.env['account.move.line'].search([], order = 'partner_id desc')
       


        grouped_dict = {}
        for line in lines :
            if line.partner_id.name in grouped_dict:
                grouped_dict[line.partner_id.name]['debit'] += line.debit
                grouped_dict[line.partner_id.name]['credit'] += line.credit
            else :
                grouped_dict[line.partner_id.name]= {'debit': line.debit, 'credit': line.credit}

        grouped_dict2 = {}
        for line in lines_total :
            if line.partner_id.name in grouped_dict2:
                grouped_dict2[line.partner_id.name]['solde_total'] += line.debit - line.credit
            else :
                grouped_dict2[line.partner_id.name] = {'solde_total': line.debit - line.credit}

        for partner in grouped_dict:
            grouped_dict[partner].update({'solde': grouped_dict[partner]['debit'] - grouped_dict[partner]['credit'],
                                          'solde_total': grouped_dict2[partner]['solde_total']  })
        return grouped_dict


    def get_date_today(self):
        return date.today()


    def get_montant_du(self):
        global montan_du
        return montan_du

    def get_previous_solde(self):
        global previous_solde
        return previous_solde


    def get_bon_ventes(self):
        """ Return invoices(bon de ventes) selon les filtres """
        move_obj = self.env['account.move']
        domain = [()]
        if self.impression_bv:
            if self.bon_de_vente == '1':
                domain = [('state', '=', 'posted'), '&',('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice'),('payment_state','in',['not_paid','partial'])]
            elif self.bon_de_vente == '2':
                this_year = date(date.today().year, 1, 1)
                next_year = date(date.today().year, 12, 31)
                domain = [('state', '=', 'posted'), '&',('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice')]
            elif self.bon_de_vente == '3':
                domain = [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice')]
            res = move_obj.search(domain)
            if self.bon_de_vente == '2':
                res = res.filtered(lambda x: x.invoice_date <= next_year and x.invoice_date >= this_year)
            self.move_ids = [(6, 0, res.ids)]



