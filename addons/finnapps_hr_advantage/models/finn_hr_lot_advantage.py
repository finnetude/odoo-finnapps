from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.finnapps_hr_advantage.tools import hr_type_bonuse_advantage

from datetime import date
import logging as log

class FinnHrLotAdvantage(models.Model):

    _name = 'finn.hr.lot.advantage'
    _description= 'Lots de prime et avantage'

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
    date_end        = fields.Date(string="Date de fin", copy=False)
    company_id      = fields.Many2one('res.company', string='Société', readonly=True, copy=False, default=lambda self: self.env.company)
    state           = fields.Selection([
                        ('draft', "Brouillon"),
                        ('open', "Confirmé"),
                        ('lock', "Bloqué"),
                        ('cancel', "Annulé"),
                        ('end', "Terminé"),], string='État', copy=False, default='draft')
    advantage_ids   = fields.One2many('finn.hr.bonuse.advantage', 'lot_id',string='Advantages')

    
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
    # @api.onchange('type_advantage')
    # def onchange_for_name(self):
    #     if self.type_advantage == False:
    #         self.write({
    #             'rule_id':False,
    #             'employee_ids':[(5, 0, 0)],
    #             'contract_ids':[(5, 0, 0)],
    #             })
    #     if self.type_advantage == 'employe':
    #         self.write({
    #             'contract_ids':[(5, 0, 0)]
    #             })
    #     if self.type_advantage == 'contract':
    #         self.write({
    #             'employee_ids':[(5, 0, 0)]
    #             })

# ======================== CRON ========================
    @api.model
    def cron_adventage_state(self):
        advantage = self.env['finn.hr.bonuse.advantage'].search([])
        for obj in advantage:
            if obj.date_end < date.today():
                obj.adv_done()

# ======================== BOUTON ========================
    def adv_draft(self):
        self.state = "draft"

    def adv_confirme(self):
        if self.type_advantage == False:
            raise ValidationError(_("Veuillez remplir le type d'avantage pour confirmer"))
        if self.rule_id == False:
            raise ValidationError(_("Veuillez remplir la règle salariale pour confirmer"))
        if self.date_start == False or self.date_end == False:
            raise ValidationError(_("Veuillez remplir les date de début et de fin pour confirmer"))
        if self.date_start > self.date_end:
            raise ValidationError(_("La date de début ne doit pas être supérieur à la date de fin, veuillez corriger pour confirmer"))

        clause_final = [('rule_id','=',self.rule_id.id), ('state','=','open'),('date_end', '>=', self.date_start), ('date_start', '<=', self.date_end)]

        lot_advantages = self.search(clause_final)

        if lot_advantages:
            for lot_advantage in lot_advantages:

                if self.type_advantage == 'employe':
                    for employe in self.employee_ids:
                        if employe in lot_advantage.employee_ids:
                            raise ValidationError(_('L\'employée "{}" a déjà un avantage "{}" en cours pendant cette période'.format(employe.name,lot_advantage.name)))
                        if employe.contract_id in lot_advantage.contract_ids:
                            raise ValidationError(_('Le contrat "{}" est déjà lié à un avantage "{}" en cours pendant cette période'.format(employe.contract_id.name,lot_advantage.name)))
            
                if self.type_advantage == 'contract':
                    for contrat in self.contract_ids:
                        if contrat.employee_id in lot_advantage.employee_ids:
                            raise ValidationError(_('L\'employée "{}" a déjà un avantage "{}" en cours pendant cette période'.format(contrat.employee_id.name,lot_advantage.name)))
                        if contrat in lot_advantage.contract_ids:
                            raise ValidationError(_('Le contrat "{}" est déjà lié à un avantage "{}" en cours pendant cette période'.format(contrat.name,lot_advantage.name)))
                        
                if self.type_advantage == 'jobs':
                    pass

        self.state = "open"

    def adv_done(self):
        self.state = "end"

    def adv_lock(self):
        self.state = "lock"

    def adv_unlock(self):
        self.state = "open"

    def adv_cancel(self):
        self.state = "cancel"
