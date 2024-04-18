# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import datetime
from calendar import monthrange

class FinnVentillationComptable(models.Model):
    _name = "finn.ventilation.comptable"
    _description = "Ventilation comptable"

    name = fields.Char('Nom',readonly=True, required=True, copy=False, default='New')
    company_id = fields.Many2one('res.company','Société',default=lambda self: self.env.company)
    year = fields.Char('Année',default=datetime.datetime.now().year)
    month = fields.Selection([('1','Janvier'),('2','Février'),('3','Mars'),
            ('4','Avril'),('5','Mai'),('6','Juin'),
            ('7','Juillet'),('8','Août'),('9','Septembre'),
            ('10','Octobre'),('11','Novembre'),('12','Décembre'),
        ],'Mois',default=str(datetime.datetime.now().month))

    ventilation_line_ids = fields.One2many('finn.ventilation.comptable.line','ventilation_id','Ligne de Ventilation comptable')
    total_payments = fields.Float('Total Versements')
    total_retenus = fields.Float('Total Retenues')
    base_ss = fields.Float('Base SS')
    retenu_ss = fields.Float('Retenu SS')

    note = fields.Text('Note')

    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        for record in self:
            if record.year and record.month:
                rec_name = "%s" % ("Ventilation comptable/ " +record.month + "/"  + record.year)
                result.append((record.id, rec_name))
        return result


    @api.onchange('month','year')
    def onchange_name(self):
        months = {'1':'Janvier','2':'Février','3':'Mars','4':'Avril',
        '5':'Mai','6':'Juin','7':'Juillet','8':'Août','9':'Septembre',
        '10':'Octobre','11':'Novembre','12':'Décembre', ' ': ' '}
        for record in self:

            record.name = "Ventilation comptable " + months[str(record.month if record.month else " ")] + " " + str(record.year if record.year else " ")
  
    

    def generate_date(self, int_year, int_month):
        var_day = monthrange(int_year, int_month)[1]
        var_premier_jour = datetime.date(int_year, int_month, 1) # Premier jour du mois
        var_dernier_jour = datetime.date(int_year, int_month, var_day) # Dernier jour du mois
        return var_premier_jour, var_dernier_jour



    def print_ventilation(self):
        return self.env.ref("finnapps_hr_account_reports.hr_payroll_ventilation_comptable").report_action(self)


    @api.model
    def create(self,vals):
        months = {'1':'Janvier','2':'Février','3':'Mars','4':'Avril',
        '5':'Mai','6':'Juin','7':'Juillet','8':'Août','9':'Septembre',
        '10':'Octobre','11':'Novembre','12':'Décembre', ' ': ' '}
      
        vals.update({'name' : "Ventilation comptable " + months[str(vals.get('month' ," "))] + " " + str(vals.get('year'," "))})
         
        rec = super(FinnVentillationComptable, self).create(vals)

        return rec
    def write(self,vals):

        months = {'1':'Janvier','2':'Février','3':'Mars','4':'Avril',
        '5':'Mai','6':'Juin','7':'Juillet','8':'Août','9':'Septembre',
        '10':'Octobre','11':'Novembre','12':'Décembre', ' ': ' '}
      
        vals.update({'name' : "Ventilation comptable " + months[str(vals.get('month' ,self.month))] + " " + str(vals.get('year',self.year))})
         

        rec = super(FinnVentillationComptable, self).write(vals)
 
        return rec

    def get_line_vc(self):
        #supprimer les lignes #############################################
        self.ventilation_line_ids.unlink()

        payslip = self.env['finn.hr.payslip']
        rules = self.env['finn.hr.salary.rule']


        contracts = self.env['hr.contract'].search([('struct_id.code','not in',['STCH','STCJ'])])


        employees = self.env['hr.employee'].search(['|',('active','=',True),('active','=',False),
                                                    ('contract_ids','in', contracts.ids)])

        var_premier_jour, var_dernier_jour = self.generate_date(int(self.year), int(self.month))

        payslips = payslip.search([('employee_id','in', employees.ids),
            ('date_from','<=', var_dernier_jour),
                                    ('date_to','>=', var_premier_jour),
            ])


       

        lines = self.env['finn.hr.payslip.line'].search([('id', 'in',payslips.mapped('line_ids').ids)],
                                                     order="sequence asc")

        lines_with_acc = self.env['finn.hr.payslip.line']
        for l in lines:
            if rules.search([('code','=', l.code),'|',('account_debit','!=',False),('account_credit','!=',False)]
                ,order="sequence asc"):
                lines_with_acc += l

       
        dict_lines = {}
        total_payments = 0
        total_retenus = 0
        base_ss = 0
        retenu_ss = 0
        for line in lines_with_acc :
            if rules.search([('code','=', line.code)],limit=1).account_debit:
                account = rules.search([('code','=', line.code)],limit=1).account_debit
            if rules.search([('code','=', line.code)],limit=1).account_credit:
                account = rules.search([('code','=', line.code)],limit=1).account_credit
   

            if line.code not in dict_lines.keys():
                dict_lines.update({line.code: {
                    'name': line.name,
                    'rubric': line.code,
                    'account_id': account.id,
                    'base': line.amount,
                    'payments': line.total if line.total > 0 else 0,
                    'returneds': abs(line.total) if line.total < 0 else 0,

                    }})
            else:
                dict_lines[line.code].update({
                    'base': dict_lines[line.code]['base']+ line.amount,
                    'payments': dict_lines[line.code]['payments'] + (line.total if line.total > 0 else 0),
                    'returneds': dict_lines[line.code]['returneds'] + (abs(line.total) if line.total < 0 else 0),
                    })
            total_payments += line.total if line.total > 0 else 0
            total_retenus += abs(line.total) if line.total < 0 else 0
            if line.code == "SS":
                base_ss += line.amount
                retenu_ss += abs(line.total) if line.total < 0 else 0


        
        for d in dict_lines:
            self.ventilation_line_ids += self.env['finn.ventilation.comptable.line'].create(dict_lines[d])
        self.total_payments = total_payments
        self.total_retenus = total_retenus
        self.base_ss = base_ss
        self.retenu_ss = retenu_ss
        



class FinnVentillationComptableLines(models.Model):
    _name = "finn.ventilation.comptable.line"
    _description = "Ligne de Ventilation comptable"

    name = fields.Char('Libellé')
    rubric = fields.Char('Rubrique')
    company_id = fields.Many2one('res.company','Société',default= lambda self : self.env.company)
    account_id = fields.Many2one('account.account','Compte')
    base = fields.Float('Base')
    payments = fields.Float('Versements')
    returneds = fields.Float('Retenues')

    ventilation_id = fields.Many2one('finn.ventilation.comptable')