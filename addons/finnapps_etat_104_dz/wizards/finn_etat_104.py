# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import ast
import logging as log


class FinnEtat104(models.TransientModel):
    _name = 'finn.etat.104'

    
    company_id = fields.Many2one('res.company', 'Société', default= lambda self : self.env.company )
    move_ids = fields.Many2many('account.move', compute="compute_move_ids", store="True")

    move_total_ht = fields.Float(compute="compute_move_total_ht")
    move_total_taxe = fields.Float(compute="compute_move_total_taxe")

    exercice_id = fields.Many2one(
        'finn.exercice',
        string='Exercice'
    )

    facture_brouillon = fields.Boolean(
        'Facture brouillon',
        default=False
    )

    counter = fields.Integer(compute="compute_counter")



    @api.depends('move_ids')
    def compute_counter(self):
        for record in self:
            i = 0
            for partner in record.move_ids.partner_id:
                i += 1
            record.counter = i



    

    @api.depends('exercice_id')
    def compute_move_ids(self):
        if self.exercice_id:
            self.move_ids = self.env['account.move'].search([('move_type','=','out_invoice'),
                          ('state','!=','Cancel'),
                          ('invoice_date','>=',self.exercice_id.date_from),
                          ('invoice_date','<=',self.exercice_id.date_to)])
        else:
            self.move_ids = False
            
    def calculate_total_price(self):
        customer_totals = {}
        
        for move in self.move_ids:
            customer_name = move.partner_id.name
        
            if customer_name in customer_totals:
                customer_totals[customer_name]['untaxed'] += move.amount_untaxed
                customer_totals[customer_name]['tax'] += move.amount_tax
            else:
                customer_totals[customer_name] = {'untaxed': move.amount_untaxed, 'tax': move.amount_tax, 'vat': move.partner_id.vat , 
                                                  'rc':move.partner_id.company_registry ,'nif': move.partner_id.nif ,'street': move.partner_id.street}
        return customer_totals
    
    @api.depends('exercice_id','move_ids')
    def compute_move_total_ht(self):
        if self.move_ids:
            for move in self.move_ids:
                self.move_total_ht += move.amount_untaxed
        else:
            self.move_total_ht = 0.0


    @api.depends('exercice_id','move_ids')
    def compute_move_total_taxe(self):
        if self.move_ids:
            for move in self.move_ids:
                self.move_total_taxe += move.amount_tax
        else:
            self.move_total_taxe = 0.0


    def tab_implement(self):
        list_for_tab = []
        list_for_ignore = []
        i = 0
        move_partner = self.move_ids.partner_id.ids

        taille_move_ids = len(move_partner)

        num_tab = taille_move_ids // 10
        rest = taille_move_ids % 10
        if rest!=0:
            num_tab += 1

        for i in [0]*num_tab:
            partners = self.env['res.partner'].search([('id','in',move_partner),('id','not in',list_for_ignore)], limit=10)

            list_for_ignore = list_for_ignore + partners.ids
            list_for_tab.append(partners)

        return list_for_tab
    

    def total_partner(self, id):
        move = self.env['account.move'].search([('id','in',self.move_ids.ids),('partner_id','=',id)])
        total_somme = sum(move.mapped('amount_total'))
        return total_somme


    def total_ht_partner(self, id):
        move = self.env['account.move'].search([('id','in',self.move_ids.ids),('partner_id','=',id)])
        total_somme = sum(move.mapped('amount_untaxed'))
        return total_somme


    def print_report(self):
        return self.env.ref("finnapps_etat_104_dz.action_etat").report_action(self)


    def _get_full_address(self, company_id):
        full_address = ''
        address_fields = ['street', 'street2', 'city', 'state_id', 'country_id']
        res = company_id.read(address_fields)[0]
        for af in address_fields:
            if res[af]:
                if af in address_fields[0:3]:
                    full_address += ' ' + res[af]
                else:
                    full_address += ' ' + res[af][1]
        return full_address.lstrip(' ')

