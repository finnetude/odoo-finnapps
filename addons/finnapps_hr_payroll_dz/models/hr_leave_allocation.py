from collections import defaultdict
import logging as log

from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.addons.resource.models.utils import HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.tools.date_utils import get_timedelta
from odoo.osv import expression
from calendar import monthrange

class HolidaysAllocationInherited(models.Model):
    """ Allocation Requests Access specifications: similar to leave requests """
    _inherit = 'hr.leave.allocation'
    _description = 'Holidays Allocation Inherited'

    def _process_accrual_plans(self):
        """
        This method is part of the cron's process.
        The goal of this method is to retroactively apply accrual plan levels and progress from nextcall to today
        """
        today = fields.Date.today()
        first_allocation = _("""This allocation have already ran once, any modification won't be effective to the days allocated to the employee. If you need to change the configuration of the allocation, cancel and create a new one.""")
        for allocation in self:
            level_ids = allocation.accrual_plan_id.level_ids.sorted('sequence')
            if not level_ids:
                continue
            if not allocation.nextcall:
                first_level = level_ids[0]
                first_level_start_date = allocation.date_from + get_timedelta(first_level.start_count, first_level.start_type)
                if today < first_level_start_date:
                    # Accrual plan is not configured properly or has not started
                    continue
                allocation.lastcall = max(allocation.lastcall, first_level_start_date)
                allocation.nextcall = first_level._get_next_date(allocation.lastcall)
                if len(level_ids) > 1:
                    second_level_start_date = allocation.date_from + get_timedelta(level_ids[1].start_count, level_ids[1].start_type)
                    allocation.nextcall = min(second_level_start_date, allocation.nextcall)
                allocation._message_log(body=first_allocation)
            days_added_per_level = defaultdict(lambda: 0)
            var_allocation = []
            while allocation.nextcall <= today:
                (current_level, current_level_idx) = allocation._get_current_accrual_plan_level_id(allocation.nextcall)
                current_level_maximum_leave = current_level.maximum_leave if current_level.added_value_type == "days" else current_level.maximum_leave / (allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY)
                nextcall = current_level._get_next_date(allocation.nextcall)
                # Since _get_previous_date returns the given date if it corresponds to a call date
                # this will always return lastcall except possibly on the first call
                # this is used to prorate the first number of days given to the employee
                period_start = current_level._get_previous_date(allocation.lastcall)
                period_end = current_level._get_next_date(allocation.lastcall)
                # Also prorate this accrual in the event that we are passing from one level to another
                if current_level_idx < (len(level_ids) - 1) and allocation.accrual_plan_id.transition_mode == 'immediately':
                    next_level = level_ids[current_level_idx + 1]
                    current_level_last_date = allocation.date_from + get_timedelta(next_level.start_count, next_level.start_type)
                    if allocation.nextcall != current_level_last_date:
                        nextcall = min(nextcall, current_level_last_date)
                var_allocation.append(allocation._process_accrual_plan_level(
                    current_level, period_start, allocation.lastcall, period_end, allocation.nextcall))
                days_added_per_level[current_level] += allocation._process_accrual_plan_level(
                    current_level, period_start, allocation.lastcall, period_end, allocation.nextcall)
                if current_level_maximum_leave > 0 and sum(days_added_per_level.values()) > current_level_maximum_leave:
                    days_added_per_level[current_level] -= sum(days_added_per_level.values()) - current_level_maximum_leave
                allocation.lastcall = allocation.nextcall
                allocation.nextcall = nextcall
            
            if days_added_per_level:
                number_of_days_to_add = allocation.number_of_days + sum(days_added_per_level.values())
                max_allocation_days = current_level_maximum_leave + (allocation.leaves_taken if allocation.type_request_unit != "hour" else allocation.leaves_taken / (allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY))
                # Let's assume the limit of the last level is the correct one
                allocation.number_of_days = min(number_of_days_to_add, max_allocation_days) if current_level_maximum_leave > 0 else number_of_days_to_add
                
                obj = self.env['finn.hr.annual.leave'].search([])
                m = datetime.now().date().month
                y = datetime.now().date().year
                cal = monthrange(y, m)[1]
                date_debut = datetime.now().date().replace(day=1)
                date_fin = datetime.now().date().replace(day=cal,month=m,year=y)
                
                leave_amount = 0
                payslip_id  = self.env['finn.hr.payslip'].search([('employee_id','=',allocation.employee_id.id),('date_from','=',date_debut),('date_to','=',date_fin)],limit=1)
                if payslip_id:
                    for line in payslip_id.line_ids:
                        if line.code == 'MC':
                            leave_amount = line.total

                            

                date_month = datetime.now().date().month
                date_year = datetime.now().date().year
                last_day_of_month = monthrange(date_year,date_month)[1]

                obj.create({
                    "date_start" : "{}-{}-01".format(date_year,date_month),
                    "date_end" : "{}-{}-{}".format(date_year,date_month,last_day_of_month),
                    "name" : str(allocation.holiday_status_id.name) + " du " + "{}/{}/01".format(date_year,date_month) + " au " + "{}/{}/{}".format(date_year,date_month,last_day_of_month),
                    "employee_id": allocation.employee_id.id,
                    "leave_type_id" :allocation.holiday_status_id.id,
                    "allocated_days_number" : var_allocation[-1],
                    "leave_amount" : leave_amount,
                    })
