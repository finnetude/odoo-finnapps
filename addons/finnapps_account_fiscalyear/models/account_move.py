# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    period_id = fields.Many2one(
        'finn.periode',
        string='Période'
    )

    def get_period(self, move_date):
        period_id = self.env['finn.periode'].search(['&',('is_opening_date','=',False),
                                                '&',('is_closing_date','=',False),
                                                '&',('date_from','<=',move_date),
                                                    ('date_to','>=',move_date)], limit=1)
        if not period_id:
            raise ValidationError("Aucune période n'est définie pour cette date : {}".format(move_date) +
                                    '\nveuillez vous allez dans Comptabilité/Périodes.')

        return period_id

    @api.model
    def create(self, vals):
        move_id = super(AccountMove, self).create(vals)
        move_id.period_id = self.get_period(move_id.date).id
        return move_id

    def write(self, vals):
        if 'date' in vals:
            vals['period_id'] = self.get_period(vals['date']).id

        return super(AccountMove, self).write(vals)

    def post(self, invoice=False):
        for move_id in self:
            if move_id.period_id.state == 'close' and not move_id.period_id.is_closing_date:
                raise ValidationError("Il n'est pas possible de valider une pièce comptable pour une période fermée")

        return super(AccountMove, self).post()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one(
        'finn.periode',
        string='Période',
        related='move_id.period_id',
        store=True
    )