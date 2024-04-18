# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnClosePeriode(models.TransientModel):
    _name = 'finn.close.periode'

    is_confirm = fields.Boolean(string='Cocher cette case si oui')
    period_ids = fields.Many2many('finn.periode')

    def finn_confirm_close_periode(self):
        if not self.is_confirm:
            raise ValidationError('er la case <Cocher cette case si oui> pour continuer')

        self.period_ids = [(6, 0, self.env.context.get('active_ids', []))]

        periods_not_closed = []
        for period_id in self.period_ids:
            account_move_ids = self.env['account.move'].search(['&',('date','>=',period_id.date_from),
                                                                    ('date','<=',period_id.date_to)])
            if 'draft' in account_move_ids.mapped('state'):
                periods_not_closed.append(period_id.name)
            else:
                period_id.state = 'close'

        if periods_not_closed:
            body = 'Les pièces comptable pour cette ou ces périodes ne sont pas validées :'
            for period_not_closed in periods_not_closed:
                body += '\n - ' + period_not_closed

            view_id = self.env['ir.ui.view'].search([('name','=','message.error.view')])
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'finn.message.error',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id' : view_id.id,
                'target': 'new',
                'context': {
                    'default_body': body,
                }
            }

            