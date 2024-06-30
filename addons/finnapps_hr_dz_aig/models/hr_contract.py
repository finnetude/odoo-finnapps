# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging as log

class HrContract(models.Model):

    _inherit = 'hr.contract'

    echelon = fields.Monetary(
    string = ('Echelon'),
    )

    dom_salaire = fields.Boolean(
        "Domiciliation du salaire"
    )
    socio_prof = fields.Char(
        "Catégorie socioprofessionnelle "
    )
