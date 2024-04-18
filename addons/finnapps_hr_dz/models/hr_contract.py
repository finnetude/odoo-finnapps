# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

import logging as log

# Mode de paiement
class FinnHrModePay(models.Model):
    _name = 'finn.hr.payement.mode'
    _description = 'Mode de paiement'
    name = fields.Char(string='Name')

class HrContract(models.Model):

    _inherit = 'hr.contract'
    _order = 'date_start asc'
    
    
    def action_view_contract_wizard(self):
        contracts = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)], order='date_start asc')
        created_id = self.env['finn.hr.contract.report'].create(
            {'employee_id': self.employee_id.id or False,
            
            'contract_ids': contracts or False,
            
             })

        return self.env['finn.hr.contract.report'].finn_wizard_view_report(created_id.id)

    exp_prec = fields.Float(
        string="Expérience précédente", 
        help="Experience accomplie dans les autres secteurs d’activité",
    )

    check = fields.Char(
        related='structure_type_id.name',
    )

    is_intern = fields.Boolean()

    total_years = fields.Float(
        default=0, 
            )

    trial_date_start = fields.Date(
        string="Début de la période d'essai",
    )

    #CONTRAT ANEM
    contrat_anem = fields.Boolean(string='Contrat ANEM',default=False)
    dispositif = fields.Many2one('finn.hr.dispositif',string='Dispositif',)
    contrat = fields.Many2one('finn.hr.contract.anem',string='Contrat',)
    type_contrat = fields.Many2one('finn.hr.contract.type.anem',string='Type de Contrat',)
    num_des = fields.Char(string="N° Décision")
    debut_contrat_anem = fields.Date(
        string='Date de début',
    )
    fin_contrat_anem = fields.Date(
        string='Date de fin',
    )
    full_name1 = fields.Char(string='Nom de contrat',
        )
    note = fields.Char(string='Note')
    state_anem = fields.Selection([
        ('draft', "Nouveau"),
        ('open', "A l'étude "),
        ('close', "Accordé"),
        ('cancel', "Rejeté"),
        ('end', "Terminer"),
    ], string='Etat', group_expand='_expand_states', copy=False,
       tracking=True, help='Status of the contract', default='draft')
    
    payement_mode = fields.Many2one(
        'finn.hr.payement.mode', 
        string='Mode de paiement',
        default=lambda self: self.env['finn.hr.payement.mode'].search([], limit=1))

    motif1 = fields.Many2one('finn.hr.reason.end.contract', string='Motif de fin de contrat',)
    
    base_mois = fields.Integer(related="resource_calendar_id.base_mois", readonly=False)

    attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel',  'record_relation_id', 'attachment_id', string="Attachments")

    iep = fields.Many2one('finn.pay.iep', string="IEP")
    iep_pourcentage = fields.Float(default=0)

    ####################### A FAIRE #######################################################
    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)

        # Récupération du type <Congés payés>
        types = self.env.ref('hr_holidays.holiday_status_cl')
        log.warning("================>{}".format(types))

        #Attribution provisionnelle de 2.5 Jours de congés
        if res.structure_type_id.name not in ['Consultant','Stagiaire']:
            log.warning("-----------------Hello Odoo")

            allocation = self.env['hr.leave.allocation'].search([
                ('employee_id','=',res.employee_id.id),('allocation_type','=','accrual')
                ])
            log.warning("Allocation:::::::::::::{}".format(allocation))
            allocation_day = 0
            if res.base_mois == 22:
                allocation_day = 1.84
            elif res.base_mois == 26:
                allocation_day = 2.17
            elif res.base_mois == 30:
                allocation_day = 2.50

            if not allocation:
                log.warning("+++++++++++++")
                accrual_leave = self.env['hr.leave.accrual.plan'].create({
                    'name': "Congé {} j/m".format(allocation_day),
                    'time_off_type_id': types.id ,
                    'transition_mode': 'immediately',
                    
                    })

                rule = self.env['hr.leave.accrual.level'].create({
                    'added_value': allocation_day,
                    'frequency' : 'monthly',
                    'first_day_display': '1',
                    'accrual_plan_id': accrual_leave.id,
                    })
                
                allocation_conge = self.env['hr.leave.allocation'].sudo().create({
                        'name': "Congé {} j/m".format(allocation_day),
                        'holiday_status_id': types.id ,
                        'allocation_type': 'accrual',
                        'date_from': res.date_start,
                        'date_to': res.date_end,
                        'holiday_type': 'employee',
                        #'employee_ids': [(4, res.employee_id.id)],
                        'employee_id': res.employee_id.id,
                        'number_of_days_display': 0,
                        'number_of_hours_display': 0,
                        'number_of_days': 0,})
        return res

    ###############################################

    @api.onchange('dispositif','contrat','type_contrat')
    def on_change_name(self):
        
        display_dispositif = ''
        display_contrat = ''
        display_type_contrat = ''

        for record in self:
            if record.dispositif.code:
                if record.contrat or record.type_contrat:
                    display_dispositif = record.dispositif.code+"/"
                else:
                    display_dispositif = record.dispositif.code
            else:
                display_dispositif = ''
            if record.contrat.code:
                if record.type_contrat:
                    display_contrat = record.contrat.code+"/"
                else:
                    display_contrat = record.contrat.code
            else:
                display_contrat = ''

            if record.type_contrat.code:
                display_type_contrat = record.type_contrat.code
            else:
                display_type_contrat = ''

            if record.dispositif or record.contrat or record.type_contrat:
                record.full_name1 = display_dispositif + display_contrat + display_type_contrat
            else:
                record.full_name1 = 'Contrat ANEM'

    @api.onchange('date_start')
    def onchange_state_date_start(self):
        if self.state == 'cancel' or not self.date_start:
            return
        if self.date_start <= date.today():
            self.state = 'open'
        elif self.date_start > date.today():
            self.state ='draft'
            
    @api.onchange('date_end')
    def onchange_state_date_end(self):
        if self.state == 'cancel' or not self.date_end:
            return
        if self.date_end <= date.today():
            self.state = 'close'
        elif self.date_end > date.today():
            self.state ='open'



    @api.onchange('check')
    def onchange_is_intern(self):
        for record in self:
            if record.check == "Stagiaire":
                record.is_intern = True




# Motif de fin de contrat
class FinnHrReasonEndContract(models.Model): 
    _name = 'finn.hr.reason.end.contract'
    _description = 'Motif de fin de contrat'
    name = fields.Char(string='Name')

# Dispositif ANEM
class FinnHrDispositif(models.Model):
    _name = 'finn.hr.dispositif'
    _description = 'Dispositif ANEM'
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    @api.depends('name','code')
    def finn_name_get(self):
        res = super(HrDispositif, self).finn_name_get()
        data1 = []
        for record in self:
            if record.name and record.code:
                display_value = record.code +":" +record.name 
            if record.name and not record.code:
                display_value = record.name 
            if not record.name and record.code:
                display_value = record.code
            if not record.name and not record.code:
                display_value = 'Dispositif'

            data1.append((record.id, display_value))

        return data1  

# Gestion du contrat avec l'ANEM
class FinnHrContractAnem(models.Model):
    _name = 'finn.hr.contract.anem'
    _description = 'Gestion du contrat avec l\'ANEM'
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    @api.depends('name','code')
    def finn_name_get(self):
        res = super(FinnHrContractAnem, self).finn_name_get()
        data2 = []
        for record in self:
            if record.name and record.code:
                display_value = record.code +":" +record.name 
            if record.name and not record.code:
                display_value = record.name 
            if not record.name and record.code:
                display_value = record.code
            if not record.name and not record.code:
                display_value = 'Dispositif'

            data2.append((record.id, display_value))

        return data2 

# Type de contrat de l'ANEM
class FinnHContratrTypeAnem(models.Model):
    _name = 'finn.hr.contract.type.anem'
    _description = 'Type de contrat de l\'ANEM'
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    @api.depends('name','code')
    def finn_name_get(self):
        res = super(FinnHContratrTypeAnem, self).finn_name_get()
        data3 = []
        for record in self:
            if record.name and record.code:
                display_value = record.code +":" +record.name 
            if record.name and not record.code:
                display_value = record.name 
            if not record.name and record.code:
                display_value = record.code
            if not record.name and not record.code:
                display_value = 'Dispositif'

            data3.append((record.id, display_value))

        return data3
