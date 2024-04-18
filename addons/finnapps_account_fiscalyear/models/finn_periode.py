# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ELoPeriode(models.Model):
    _name = 'finn.periode'

    name = fields.Char(
        string='Période'
    )

    date_from = fields.Date(
        string='Date de début'
    )

    date_to = fields.Date(
        string='Date de fin'
    )

    code = fields.Char(
        string='Code'
    )

    exercice_id = fields.Many2one(
        'finn.exercice',
        string='Exercice'
    )

    is_opening_date = fields.Boolean(
        string='Période de d’ouverture'
    )

    is_closing_date = fields.Boolean(
        string='Période de clôture'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company.id
    )
    state = fields.Selection(
        string='État',
        selection=[('open', 'Ouverte'), ('close', 'Fermée')],
        default='open',
    )

    def finn_close_periode(self):
        view_id = self.env['ir.ui.view'].search([('name','=','close.periode.view')])

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'finn.close.periode',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id' : view_id.id,
            'target': 'new',
            'context': {
                'default_period_ids': [(6, 0, [self.id])],
            }
        }

    @api.model
    def finn_remplir_les_periodes(self):

        move_names = ''
        move_ids = self.env['account.move'].search([('period_id','=',False)])

        for move_id in move_ids:
            period_id = self.env['finn.periode'].search(['&',('is_opening_date','=',False),
                                                    '&',('is_closing_date','=',False),
                                                    '&',('date_from','<=',move_id.date),
                                                        ('date_to','>=',move_id.date)], limit=1)
            if not period_id:
                move_names += ' ' + move_id.name + ','
            else:
                move_id.period_id = period_id.id

        if move_names:
            raise ValidationError("Les pièces qu'ont pas des périodes sont : " + move_names)


