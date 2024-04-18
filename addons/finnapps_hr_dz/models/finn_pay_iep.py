# -*- coding: utf-8 -*-
from odoo import models, fields

class FinnPayIep(models.Model):

    _name = 'finn.pay.iep'
    _description = "Indemnité de l\'expérience professionnelle"

    year = fields.Integer(
        string="sur combien d'année", 
        default=0,
    )

    taux = fields.Float(
        string="TAUX %", 
        default=0,
    )

    year_application = fields.Integer(
        string="A partir de ?", 
        default=0,
    )

    name = fields.Char(
        compute='finn_make_name',
    )

    def finn_make_name(self):
        for record in self:
            record.name = str(record.taux)+ ' tout les ' +str(record.year)+' ans à partir de ' +str(record.year_application)+ ' ans'


