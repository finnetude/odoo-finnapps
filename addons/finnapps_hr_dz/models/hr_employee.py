# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
import logging as log

class employee(models.Model):

    _inherit = 'hr.employee'
    
    contrat_state = fields.Selection(related = "contract_id.state")

    agency_id           = fields.Many2one('res.partner', string='Agence', domain="[('is_cnas_agency', '=', True)]")
    payment_center_id   = fields.Many2one('res.partner', string='Centre de paiement', domain="[('parent_id', '=', agency_id),('is_payment_center', '=', True)]")

    nat_cot1 = fields.Selection(
        [('R22', 'R22 : Régime generale'),
        ('R06', 'R06 : Abattement de 40% sur taux de cotisations'),
    #    ('R...', 'R... : Abattement de 50% sur taux de cotisations'), EN ATTENTE DE PLUS D'INFORMATION
        ('R07', 'R07 : Abattement de 80% sur taux de cotisations'),
        ('R08' , 'R08 : Abattement de 90% sur taux de cotisations')],
        string="Nature des cotisations",
        default='R22'
    )

    blood_group = fields.Selection(
        [('ap','A+'),
        ('am','A-'),
        ('bp','B+'),
        ('bm','B-'),
        ('abp','AB+'),
        ('abm','AB-'),
        ('op','O+'),
        ('om','O-')],
        string="Groupe sanguin",
        default='ap'
    )

    disabled_or_retirement = fields.Boolean(default=False, string="Retraité / Handicapé")

    mutual_restraint = fields.Boolean(string="Retenue mutuelle", default=False)
    mutual_percentage = fields.Integer(string="Pourcentage de retenue mutuelle")
    cacobath = fields.Boolean(string="Cacobath", default=False)

    avnt_social = fields.Boolean(string="Avantages sociaux", default=False)
    num_des_abattement = fields.Char( string="N° décision abattement")
    debut_abattement = fields.Date(string="Début de l’abattement")
    fin_abattement = fields.Date(string="Fin de l’abattement")
    
    @api.onchange('agency_id')
    def onchange_payment_center(self):
        self.payment_center_id = False
        
    @api.model
    def _get_gender(self):
        selection = [
            ('male', 'Male'),
            ('female', 'Female')
        ]
        return selection

    gender = fields.Selection(selection=_get_gender , string='Gender')

    spouse_complete_name = fields.Char(string="Nom complet de l'époux (se)", groups="hr.group_hr_user", tracking=True)

    def calcul_date(self, value):
        # Calcul  Now's date - number of days (value)
        day = datetime.now().day - value 
        month = datetime.now().month
        year = datetime.now().year

        if day < 1:
            if month in [1,3,5,7,8,10,12]:
                day = 31 + day 
            elif month == 2 :
                if (year % 4) == 0:
                    if (year % 100) == 0:
                        if (year % 400) == 0:
                            day = 29 + day
                        else:
                            day = 28 + day
                    else:
                        day = 29 + day
                else:
                    day = 28 + day
            else :
                day = 30 + day 
            month -= 1
            if month < 1 :
                month = 12
                year -= 1
        return datetime.now().replace(day=day, month=month, year=year)

    @api.model
    def remove_some_resource_calendar(self):
        res = self.env['resource.calendar'].search([ 
            ('name', '=', 'Standard 35 hours/week')
            ]).unlink()
        res = self.env['resource.calendar'].search([ 
            ('name', '=', 'Standard 38 hours/week')
            ]).unlink()
        
    @api.model
    def remove_standard_40_hours_week(self):
        res = self.env['resource.calendar'].search([ 
            ('name', '=', 'Standard 40 hours/week')
            ])
        res.active = False
        self.env.company.resource_calendar_id = self.env['resource.calendar'].search([],limit=1)
