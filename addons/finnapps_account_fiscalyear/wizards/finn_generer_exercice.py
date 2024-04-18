# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnGenererExercice(models.TransientModel):
    _name = 'finn.generer.exercice'

    date_from = fields.Date(
        string='Date de début'
    )

    date_to = fields.Date(
        string='Date de fin'
    )

    type_de_periode = fields.Selection(
        string='Type de période',
        selection=[('quarterly', 'Trimestrielle'), ('monthly', 'Mensuelle')],
    )

    #Un champ booléen pour vérifer le type de période
    tri_ou_men = fields.Boolean(
        string='Pour type de période',
        compute='finn_check_tri_ou_men')
    #Une fonction qui retourne tri_ou_men (vrai si type de période = 'Mensuelle' et faux si ype de période = 'Trimestrielle')
    def finn_check_tri_ou_men(self):
        if self.type_de_periode == 'quarterly':
            self.tri_ou_men = False
        else:
            self.tri_ou_men = True


    def finn_generer_exercice(self):
        #self.check_year()
        self.finn_check_period()

        exercice_id = self.env['finn.exercice'].create({
            'name': str(self.date_from.year),
            'code': str(self.date_from.year),
            'date_from': self.date_from,
            'date_to': self.date_to,
            'tri_ou_men': self.tri_ou_men,
        })

        if self.type_de_periode == 'quarterly':
            exercice_id.finn_create_period_quarterly()
        else:
            exercice_id.finn_create_period_monthly()

        view_id = self.env.ref('finnapps_account_fiscalyear.exercice_form_view')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'finn.exercice',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id' : view_id.id,
            'res_id':exercice_id.id,
        }

    # def check_year(self):
    #     if self.date_from.year != self.date_to.year:
    #         raise ValidationError('La période de cet exercice doit se trouver sur une même année')

    def finn_check_period(self):
        if self.date_to < self.date_from:
            raise ValidationError('Période incorrecte')