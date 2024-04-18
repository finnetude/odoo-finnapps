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

class FinnHrPayslipInput(models.Model):
    _name = 'finn.hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(
        string='Description', 
        required=True
        )

    payslip_id = fields.Many2one(
        'finn.hr.payslip', 
        string='Feuille de paie', 
        required=True, 
        ondelete='cascade', 
        index=True
        )

    sequence = fields.Integer(
        required=True, 
        string="Séquence", 
        index=True, 
        default=10
        )

    code = fields.Char(
        required=True, 
        help="Code qui peut être utilisé dans les règles salariales"
        )

    amount = fields.Float(
        help="It is used in computation. For e.g. A rule for sales having "
               "1% commission of basic salary for per product can defined in expression "
               "like result = inputs.SALEURO.amount * contract.wage*0.01.", 
        string="Montant"
        )

    contract_id = fields.Many2one(
        'hr.contract', 
        string='Contrat', 
        required=True,
        help="The contract for which applied this input"
        )
