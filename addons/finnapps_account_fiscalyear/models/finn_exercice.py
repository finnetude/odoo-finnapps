# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime 
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
import calendar
from odoo.exceptions import ValidationError


class Finn_Exercice(models.Model):
    _name = 'finn.exercice'

    name = fields.Char(
        string='Fiscalyear'
    )

    date_from = fields.Date(
        string='Start Date'
    )

    date_to = fields.Date(
        string='End date'
    )

    code = fields.Char(
        string='Code'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Year end operations journal"
    )

    period_ids = fields.One2many(
        'finn.periode',
        'exercice_id',
        string="Periods"
    )

    have_periods = fields.Boolean(
        default=False
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company.id
    )
    state = fields.Selection(
        string='State',
        selection=[('open', 'Open'), ('close', 'Close')],
        default='open',
    )
    tri_ou_men = fields.Boolean(
        string='For period type')

    _sql_constraints = [
        ('unique_code', 'UNIQUE (code,company_id)', "The exercise code already exists"),
        ('unique_name', 'UNIQUE (name,company_id)', "The exercise name already exists")
    ]


    def finn_last_day_of_month(self ,any_day):
        # this will never fail
        # get close to the end of the month for any day, and add 4 days 'over'
        next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
        # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
        return next_month - datetime.timedelta(days=next_month.day)

    def finn_getQuarterStart(self, any_day):
        return datetime.date(any_day.year, (any_day.month - 1) // 3 * 3 + 1, 1)

    def finn_getQuarterEnd(self, any_day):
        quarterStart = self.finn_getQuarterStart(any_day)
        return quarterStart + relativedelta(months=3, days=-1)

    def finn_create_period_quarterly(self):
        self.ensure_one()
        self.with_context({'period_monthly': 3}).finn_create_period_monthly()
        return True

    def finn_create_period_monthly(self):
        self.ensure_one()
        #self.check_year()
        self.finn_check_period()

        interval = self._context.get('period_monthly') or 1
        period_obj = self.env['finn.periode']
        date_from = self.date_from
        if self.date_from.year == self.date_to.year:
            date_o_f = '{}'.format(self.date_from.year)
        else:
            date_o_f = '{}-{}'.format(self.date_from.year ,self.date_to.year)

        period_obj.create({
            'name':  "Période d'ouverture " + date_o_f,
            'code': date_from.strftime('00/%Y'),
            'date_from': date_from,
            'date_to': date_from,
            'is_opening_date': True,
            'exercice_id': self.id,
        })
        dicto = []
        while date_from < self.date_to:
            date_to = self.finn_last_day_of_month(date_from) if interval==1 else self.finn_getQuarterEnd(date_from)

            if date_to > self.date_to:
                date_to = self.date_to
            period_obj.create({
                'name': date_from.strftime('%m/%Y'),
                'code': date_from.strftime('%m/%Y'),
                'date_from': date_from,
                'date_to': date_to,
                'exercice_id': self.id,
            })
            date_from = date_to + datetime.timedelta(days=1)

        period_obj.create({
            'name': 'Période de clôture ' + date_o_f,
            'code': self.date_to.strftime('99/%Y'),
            'date_from': self.date_to,
            'date_to': self.date_to,
            'is_closing_date': True,
            'exercice_id': self.id,
        })
        self.have_periods = True

        return True


    # def check_year(self):
    #     if self.date_from.year != self.date_to.year:
    #         raise ValidationError('La période de cet exercice doit se trouver sur une même année')

    def finn_check_period(self):
        if self.date_to < self.date_from:
            raise ValidationError('Période incorrecte')
