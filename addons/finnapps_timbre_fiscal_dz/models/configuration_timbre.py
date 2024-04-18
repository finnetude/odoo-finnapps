# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from math import ceil
import logging as log

class ResCompany(models.Model):
    _inherit = 'res.company'


    based_on =   fields.Selection(
        [('posted_invoices', 'Factures validées'),
         ('payment', 'Paiements des factures')],default="payment", string="Se baser sur",required=True)


    tranche = fields.Float(
        string="Tranche",
        required=True,
        default=0.0,
    )

    prix = fields.Float(
        string="Pourcentage",
        required=True,
        default=0.0,
    )

    # comptes contreparties vente
    sale_timbre = fields.Many2one(
        comodel_name='account.account',
        string="Compte contrepartie vente"
    )


    # Montant Minimal TTC
    mnt_min = fields.Float(
        string="Montant minimal",
        required=True,
        default=0.0,
    )

    # Montant Maximal TTC
    mnt_max = fields.Float(
        string="Montant maximal",
        required=True,
        default=0.0,
    )
    _sql_constraints = [
        ('Montant_check', 'CHECK(mnt_max >= mnt_min)','Le montant maximal doit être supérieur au montant minimal ')
        ]


    montant_en_lettre = fields.Boolean(
        string="Afficher le montant en lettre sur l’impression des factures",
    )
    
   
    @api.model
    def _timbre(self, montant):
        montant_avec_timbre = 0.0
        if not self :
            raise UserError(_('Pas de configuration du calcul Timbre.'))

        if montant >= self.mnt_min and montant <= self.mnt_max:
            if self.tranche:
                montant_avec_timbre = (montant * self.prix) / self.tranche
        if montant > self.mnt_max:
         
            if self.tranche:
                montant_avec_timbre = (self.mnt_max * self.prix) / self.tranche

        return montant_avec_timbre

    @api.onchange('tranche', 'prix', 'mnt_min', 'mnt_max')
    def chek_negative_values(self):
        for record in self:
            if record.tranche < 0:
                record.update({'tranche': (record.tranche * -1),})
            if record.prix < 0:
                record.update({'prix': (record.prix * -1),})
            if record.mnt_min < 0:
                record.update({'mnt_min': (record.mnt_min * -1),})
            if record.mnt_max < 0:
                record.update({'mnt_max': (record.mnt_max * -1),})

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pay_invoices_online = fields.Boolean("Pay Invoices Online", help="Enable online payment for invoices.")
    based_on =   fields.Selection(
        [('posted_invoices', 'Factures validées'),
         ('payment', 'Paiements des factures')],default="payment", string="Se baser sur",required=True)

    
    tranche = fields.Float(
        string="Tranche",
        required=True,
        readonly=False,
        default=0.0,
    )

    prix = fields.Float(
        string="Pourcentage",
        required=True,
        readonly=False,
        default=0.0,
    )

    # comptes contreparties vente
    sale_timbre = fields.Many2one(
        comodel_name='account.account',
        readonly=False,
        string="Compte contrepartie vente"
    )


    # Montant Minimal TTC
    mnt_min = fields.Float(
        string="Montant minimal",
        required=True,
        readonly=False,
        default=0.0,
    )

    # Montant Maximal TTC
    mnt_max = fields.Float(
        string="Montant maximal",
        required=True,
        readonly=False,
        default=0.0,
    )

    montant_en_lettre = fields.Boolean(
        string="Afficher le montant en lettre sur l’impression des factures",
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company

        company and res.update(
            tranche= company.tranche,
            prix= company.prix,
            sale_timbre= company.sale_timbre.id,
            mnt_min= company.mnt_min,
            mnt_max= company.mnt_max,
            montant_en_lettre= company.montant_en_lettre,
            based_on= company.based_on,

        )
        return res


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        company = self.env.company
        company and company.write({
            'tranche': self.tranche,
            'prix': self.prix,
            'sale_timbre': self.sale_timbre.id,
            'mnt_min': self.mnt_min,
            'mnt_max': self.mnt_max,
            'montant_en_lettre': self.montant_en_lettre,
            'based_on': self.based_on,
        })
        return res
