from datetime import date
import logging as log
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.finnapps_hr_advantage.tools import hr_type_bonuse_advantage

class FinnHrBonuseAdvantage(models.Model):

    _name = 'finn.hr.bonuse.advantage'
    _description= 'Primes et avantages'

# ======================== DOMAINE ========================
    def _domain_for_rule(self):
        rules = []
        # Ne pas prendre les catégories - base - Brut - Net - heure par jour - intermédiaire - coéfficiant
        categorys = self.env['finn.hr.salary.rule.category'].search([('code','in',['BASIC','GROSS','NET','HJ','INTERM','COEFF'])]).ids
        # Ne pas prendre les régulations  et da'autre
        rules_no_us = hr_type_bonuse_advantage.codes_hr_salary_ruels_spe + hr_type_bonuse_advantage.codes_hr_salary_ruels_reg
        rules = self.env['finn.hr.salary.rule'].search([('category_id','not in',categorys),('code','not in',rules_no_us)]).ids
        return [('id','in',rules)]

# ======================== CHAMPS ========================
    name            = fields.Char(string="Nom", compute="_compute_name")
    description     = fields.Text(string='Description')
    type_advantage  = fields.Selection([
                        # ('all', "Tous"),
                        ('employe', "Employé"),
                        ('contract', "Contrat"),
                        ('job', "Poste"),],
                        string="Type d'avantage", copy=False)
    rule_id         = fields.Many2one('finn.hr.salary.rule', string='Règle salariale', domain=_domain_for_rule)
    code            = fields.Char(string="Référence", compute="_compute_code")
    category_id     = fields.Many2one('finn.hr.salary.rule.category', string='Catégorie', compute="_compute_category")
    date_start      = fields.Date(string="Date de début", copy=False)
    is_infinity     = fields.Boolean(string = "l'infinie",default=True)
    date_end        = fields.Date(string="Date de fin",default=datetime.datetime.today(), copy=False)
    employee_ids    = fields.Many2many('hr.employee', 'hr_advantage_employee_employee', 'advantage_employee_id', 'employee_id', string='Employé(s)', copy=False)
    contract_ids    = fields.Many2many('hr.contract', 'hr_advantage_employee_contract', 'advantage_contract_id', 'contract_id', string='Contrats', copy=False)
    job_ids         = fields.Many2many('hr.job', 'hr_advantage_employee_hr_job', 'advantage_job_id', 'job_id', string='Postes de travail', copy=False)
    company_id      = fields.Many2one('res.company', string='Société', readonly=True, copy=False, default=lambda self: self.env.company)
    amount_adv      = fields.Float(string='Montant', default=0)
    state           = fields.Selection([
                        ('draft', "Brouillon"),
                        ('open', "Confirmé"),
                        ('lock', "Bloqué"),
                        ('cancel', "Annulé"),
                        ('end', "Terminé"),], string='Etat', copy=False, default='draft')
    lot_id          = fields.Many2one('finn.hr.lot.advantage', string='Lot de prime et avantage')

# ======================== COMPUTE ========================
    @api.depends('rule_id')
    def _compute_code(self):
        for record in self:
            record.code = record.rule_id.code

    @api.depends('rule_id')
    def _compute_category(self):
        for record in self:
            record.category_id = record.rule_id.category_id.id

    @api.depends('rule_id')
    def _compute_name(self):
        for record in self:
            if record.rule_id:
                record.name = "{} ({})".format(record.rule_id.category_id.name, record.rule_id.code)
            else:
                record.name = ""

# ======================== ONCHANGE ========================
    @api.onchange('type_advantage')
    def onchange_for_name(self):
        if self.type_advantage == False:
            self.write({
                'rule_id':False,
                'employee_ids':[(5, 0, 0)],
                'contract_ids':[(5, 0, 0)],
                })
        if self.type_advantage == 'employe':
            self.write({
                'contract_ids':[(5, 0, 0)]
                })
        if self.type_advantage == 'contract':
            self.write({
                'employee_ids':[(5, 0, 0)]
                })

# ======================== CRON ========================
    @api.model
    def finn_cron_adventage_state(self):
        advantage = self.env['finn.hr.bonuse.advantage'].search([])
        for obj in advantage:
            if(obj.is_infinity):
                if obj.date_end < date.today():
                    obj.adv_done()

# ======================== BOUTON ========================
    def adv_draft(self):
        self.state = "draft"

    def adv_confirme(self):
        log.info(self)
        if self.type_advantage == False:
            raise ValidationError(_("Veuillez remplir le type d'avantage pour confirmer"))
        if self.rule_id == False:
            raise ValidationError(_("Veuillez remplir la règle salariale pour confirmer"))
        if self.date_start == False and self.is_infinity == True:
            raise ValidationError(_("Veuillez remplir les date de début "))
        elif (self.date_end == False or self.date_start == False) and self.is_infinity == False : 
            raise ValidationError(_("Veuillez remplir les date de début et de fin pour confirmer"))
        if self.date_start > self.date_end and self.is_infinity == False:
            raise ValidationError(_("La date de début ne doit pas être supérieur à la date de fin, veuillez corriger pour confirmer"))
        if not self.contract_ids and self.type_advantage == 'contract':
            raise ValidationError(_("Veuillez renseigner un contrat pour confirmer"))

        clause_final = [('rule_id','=',self.rule_id.id), ('state','=','open')]
    #,('date_end', '>=', self.date_start), ('date_start', '<=', self.date_end)
        advantages = self.search(clause_final)

        if advantages:
            for advantage in advantages:

                if self.type_advantage == 'employe':
                    for employe in self.employee_ids:
                        if employe in advantage.employee_ids:
                            raise ValidationError(_('L\'employée "{}" a déjà un avantage "{}" en cours pendant cette période'.format(employe.name,advantage.name)))
                        if employe.contract_id in advantage.contract_ids:
                            raise ValidationError(_('Le contrat "{}" est déjà lié à un avantage "{}" en cours pendant cette période'.format(employe.contract_id.name,advantage.name)))
            
                if self.type_advantage == 'contract':
                    for contrat in self.contract_ids:
                        if contrat.employee_id in advantage.employee_ids:
                            raise ValidationError(_('L\'employée "{}" a déjà un avantage "{}" en cours pendant cette période'.format(contrat.employee_id.name,advantage.name)))
                        if contrat in advantage.contract_ids:
                            raise ValidationError(_('Le contrat "{}" est déjà lié à un avantage "{}" en cours pendant cette période'.format(contrat.name,advantage.name)))
        self.state = "open"

    def adv_done(self):
        self.state = "end"

    def adv_lock(self):
        self.state = "lock"

    def adv_unlock(self):
        self.state = "open"

    def adv_cancel(self):
        self.state = "cancel"
