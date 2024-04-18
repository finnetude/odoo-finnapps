import babel
from  calendar import monthrange
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

from math import *

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.tools import float_compare, float_is_zero
import logging as log



class FinnHrPayslipRun(models.Model):
    _name = 'finn.hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(
        required=True
        )

    slip_ids = fields.One2many(
        'finn.hr.payslip', 
        'payslip_run_id', 
        string='Feuilles de paie'
        )


    state = fields.Selection([
        ('draft', 'Broullion'),
        ('done', 'Fait'),
        ('close', 'Fermer'),
    ], string='Statut', 
        index=True, 
        readonly=True, 
        copy=False, 
        default='draft'
        )

    date_start = fields.Date(
        string='Date Début', 
        required=True, 
        default=lambda self: fields.Date.to_string(date.today().replace(day=1))
        )

    date_end = fields.Date(
        string='Date Fin', 
        required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
        )


    credit_note = fields.Boolean(
        string='Avoir', 
        help="If its checked, indicates that all payslips generated from here are refund payslips."
        )

    journal_id = fields.Many2one(
        'account.journal', 
        'Journal salarial', 
        required=True, 
        domain="[('type', '=', 'general'),('is_journal_for_pay','=',True)]", 
        default=lambda self: self.env['account.journal'].search([('type', '=', 'general'),('is_journal_for_pay','=',True)], limit=1)
        )

      
    def draft_payslip_run(self):
        return self.write({'state': 'draft'})
        #Faut remettre en broullion la pièce comptable aussi

    def close_payslip_run(self):
        return self.write({'state': 'close'})

    def done_payslip_run(self):
        for line in self.slip_ids:
            line.action_payslip_done()
        return self.write({'state': 'done'})

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('Vous ne pouvez pas supprimer les lots de fiches de paie terminés'))
        return super(FinnHrPayslipRun, self).unlink()
