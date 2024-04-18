# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
import logging as log

class ResourceCalendar(models.Model):

    _inherit = "resource.calendar"

    base_mois = fields.Integer(
        default=22,
    )

    def _get_default_attendance_ids(self):
        for record in self:
            if record.id not in ['22J','26J','30J']:
                return [
                    (0, 0, {'name': _('Monday Morning'), 'dayofweek': '0', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                    (0, 0, {'name': _('Monday Evening'), 'dayofweek': '0', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'}),
                    (0, 0, {'name': _('Tuesday Morning'), 'dayofweek': '1', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                    (0, 0, {'name': _('Tuesday Evening'), 'dayofweek': '1', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'}),
                    (0, 0, {'name': _('Wednesday Morning'), 'dayofweek': '2', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                    (0, 0, {'name': _('Wednesday Evening'), 'dayofweek': '2', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'}),
                    (0, 0, {'name': _('Thursday Morning'), 'dayofweek': '3', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                    (0, 0, {'name': _('Thursday Evening'), 'dayofweek': '3', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'}),
                    (0, 0, {'name': _('Friday Morning'), 'dayofweek': '4', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                    (0, 0, {'name': _('Friday Evening'), 'dayofweek': '4', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'})
                ]
            else:
                return []

class ResourceCalendarAttendancer(models.Model):

    _inherit = "resource.calendar.attendance"

    day_period = fields.Selection([('morning', 'Morning'),('lunch' , 'Pause') ,('afternoon', 'Afternoon') ,('night','Nuit')], required=True, default='morning')






    