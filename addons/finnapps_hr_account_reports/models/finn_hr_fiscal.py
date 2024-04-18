
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date ,timedelta

class FinnHrFiscal(models.Model):
    _name = "finn.hr.fiscal"

  
    name = fields.Char('Nom',readonly=True, required=True, copy=False, default='New')

    type = fields.Selection(selection=[('employee','Employee'),
                                        ('consultant','Consultant')] ,default='employee')

    company_id = fields.Many2one('res.company' ,default= lambda self: self.env.company)
    # first page 
    direction_impots_fr = fields.Char('Direction des impôts',
                        default= lambda self: self.env.company.state_id.name)

    centre_impots_fr = fields.Char('Centre des impôts',
                        default= lambda self: self.env.company.state_id.name)

    @api.onchange('company_id')
    def onchange_direction(self):
        for record in self:
            record.direction_impots_fr = record.company_id.state_id.name

    @api.onchange('company_id')
    def onchange_centre(self):
        for record in self:
            record.centre_impots_fr = record.company_id.state_id.name

    direction_impots_ar = fields.Char('Direction des impôts',)

    centre_impots_ar = fields.Char('Centre des impôts',)
    
    year = fields.Char(
        string="Année de déclaration",
        default=datetime.now().year,
        required=True,)

   

    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        for record in self:
            if record.year:
                rec_name = "%s" % ("301bis/" + record.year)
                result.append((record.id, rec_name))
        return result
        
    def _default_raison_sociale(self):

        name = (self.env.company.forme_juridique.code if self.env.company.forme_juridique else '') + ' ' + self.env.company.name 
        return str(name)

    raison_sociale = fields.Char('Nom',default=_default_raison_sociale)

    profession = fields.Many2one('res.partner.industry',string='Secteur d\'activité',
                        default= lambda self: self.env.company.partner_id.industry_id)

    @api.onchange('company_id')
    def onchange_raison_sociale(self):
        for record in self:
            record.raison_sociale = (record.company_id.forme_juridique.code if record.company_id.forme_juridique else '') + ' ' + record.company_id.name 
 
    @api.onchange('company_id')
    def onchange_profession(self):
        for record in self:
            record.profession = record.company_id.partner_id.industry_id


    adress = fields.Char('Adresse',
                        default= lambda self: self.env.company.street)
    nif = fields.Char(string="N.I.F" ,help='Numéro d’Identification Fiscale')

    @api.onchange('company_id')
    def onchange_nif(self):
        for record in self:
            if hasattr(record.company_id, 'nif'):
                record.nif = record.company_id.nif
            else:
                record.nif = ''


    montant = fields.Monetary('Montant des salaires bruts versés' )
    currency_id = fields.Many2one(
        'res.currency', 'Cost Currency', compute='_compute_currency_id')

    @api.depends_context('direction_impots_fr')
    def _compute_currency_id(self):
        self.currency_id = self.env.company.currency_id.id



    fiscal_rec_id = fields.One2many('finn.hr.fiscal.rec','fiscal_id')
    fiscal_droit_id = fields.One2many('finn.hr.fiscal.droit','fiscal_id')




    note_fiscal_droit = fields.Text('Note' ,default="""
                1. NATURE des impôts et taxes
                2. Sommes payées en éspèces
                3. Rémunérationsallouées en nature
                4. Salaires imposables
                5. Pourboire indemnités diverses
                6. Montant net des sommes imposables (col,2 + col. 3 + col. 4 + col. 5)
                7. Montant total des sommes dues
                8. Montant total des sommes versées
                9. RESTE DUE ou trop versé
                                        """
                                        )
    note_fiscal = fields.Text('Note' ,default="""
                La date de la quittance: c'est la date de dépôt de rapport G50
                                        """
                                        )

    fiscal_emp_id = fields.One2many('finn.hr.fiscal.emp','fiscal_id', relation="rel1")
    fiscal_emp_id2 = fields.One2many('finn.hr.fiscal.emp','fiscal_id', relation="rel2")
    fiscal_emp_id3 = fields.One2many('finn.hr.fiscal.emp','fiscal_id', relation="rel3")
    fiscal_emp_id4= fields.One2many('finn.hr.fiscal.emp','fiscal_id', relation="rel4")


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('seq_fiscal') or 'New'

        return super(FinnHrFiscal,self).create(vals)


    @api.onchange('fiscal_emp_id')
    def onchange_fiscal_emp(self):
        for record in self:
            record.fiscal_emp_id2 = record.fiscal_emp_id3 = record.fiscal_emp_id4 = record.fiscal_emp_id
        

    def calculer_lignes(self):


        #supprimer les lignes #############################################
        self.fiscal_rec_id.unlink()
        self.fiscal_droit_id.unlink()
        self.fiscal_emp_id.unlink()
        self.fiscal_emp_id2.unlink()
        self.fiscal_emp_id3.unlink()
        self.fiscal_emp_id4.unlink()
        #calculer Montant #################################################
        self.montant = 0
        if self.type == 'employee':
            bulletins = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','!=','Consultant'),('date_to','>=',date(int(self.year),1,1)), ('date_to','<=',date(int(self.year),12,31))])
        if self.type == 'consultant':
            bulletins = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','=','Consultant'), ('date_to','>=',date(int(self.year),1,1)), ('date_to','<=',date(int(self.year),12,31))])

        for b in bulletins:
            montant = [m.total for m in b.line_ids if m.code == 'GROSS']
        
            self.montant += sum(montant)

        #1st table #########################################################
        recs = self.env['finn.hr.fiscal.rec']
        months = ['Mois de Janvier', 'Mois de Février', 'Mois de Mars', 'Mois de Avril', 'Mois de Mai', 'Mois de Juin' ,'Mois de Juillet', 'Mois de Âout', 'Mois de Septembre', 'Mois de Octobre', 'Mois de Novembre','Mois de Décembre' ]
        for month in months: 
            date_b = date(int(self.year),months.index(month)+1,1)
            if months.index(month)+1 < 12:
                date_a = date(int(self.year),months.index(month)+2,1) 
            else:
                date_a = date(int(self.year)+1,1,1) 

            if self.type == 'employee':
                pays = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','!=','Consultant'),('date_to','>=',date_b), ('date_to','<=',date_a - timedelta( days=1) )])
            if self.type == 'consultant':
                pays = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','=','Consultant'),('date_to','>=',date_b), ('date_to','<=',date_a - timedelta( days=1) )])

            recs += recs.create({
                    'mois': month,
                    'somme_traitement': abs(sum([p.total for p in pays.line_ids if p.code == 'SBI'] )),
                    'somme_pensions': abs(sum([p.total for p in pays.line_ids if p.code in ['IRG','IRGC']] )),
                })

        recs += recs.create({
                'mois': 'Complément 15%',
        
            })
        recs += recs.create({
                'mois': 'Montant des salaires exonérés',
        
            })
   
        total = recs.create({
                    'mois': 'Total imposable',
                    'somme_traitement': abs(sum(recs.mapped('somme_traitement'))),
                    'somme_pensions': abs(sum(recs.mapped('somme_pensions'))),
            })

        recs += total
        self.fiscal_rec_id = recs 

        #2nd table #########################################################
        droits = self.env['finn.hr.fiscal.droit']
        droits += droits.create({
                    'nature_impo': 'I.R.G. sur Salaires',
                    'salaire_impo': abs(total.somme_traitement),
                    'montant_1': abs(total.somme_traitement),
                    'montant_2': abs(total.somme_pensions),
                    'montant_3': abs(total.somme_pensions),
            })
        droits += droits.create({
                    'nature_impo': 'I.R.G. sur les Pensions',
            })
        self.fiscal_droit_id = droits

        #3rd table #########################################################
        emps = self.env['finn.hr.fiscal.emp']

        if self.type == 'employee':
            employees = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','!=','Consultant'),('date_to','>=',date(int(self.year),1,1)), ('date_to','<=',date(int(self.year),12,31))]).mapped('employee_id')
        if self.type == 'consultant':
            employees = self.env['finn.hr.payslip'].search([('contract_id.structure_type_id.name','=','Consultant'),('date_to','>=',date(int(self.year),1,1)), ('date_to','<=',date(int(self.year),12,31))]).mapped('employee_id')

        num = 1
        for employee in employees :
            emp = {
                'origin_num': num,
                'employee_id': employee.id,
                'situation' : employee.marital if employee.marital != 'cohabitant' else 'single',
                }
            pays = self.env['finn.hr.payslip'].search([('employee_id','=',employee.id),('date_to','>=',date(int(self.year),1,1)), ('date_to','<=',date(int(self.year),12,31))])
            for pay in pays:
                
                if pay.date_to.month == 1:
                    emp.update({
                        'net_jan': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_jan': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 2:
                    emp.update({
                        'net_fev': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_fev': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 3:
                    emp.update({
                        'net_mars': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_mars': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 4:
                    emp.update({
                        'net_avril': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_avril': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 5:
                    emp.update({
                        'net_mai': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_mai': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 6:
                    emp.update({
                        'net_juin': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_juin': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 7:
                    emp.update({
                        'net_juil': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_juil': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 8:
                    emp.update({
                        'net_aout': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_aout': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 9:
                    emp.update({
                        'net_sep': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_sep': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 10:
                    emp.update({
                        'net_oct': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_oct': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 11:
                    emp.update({
                        'net_nov': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_nov': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
                if pay.date_to.month == 12:
                    emp.update({
                        'net_dec': abs(sum([m.total for m in pay.line_ids if m.code == 'NET'])),
                        'retenu_dec': abs(sum([m.total for m in pay.line_ids if m.code in ['IRG','IRGC'] ])),
                        })
            emps += emps.create(emp)
            num +=1
        self.fiscal_emp_id = self.fiscal_emp_id2 = self.fiscal_emp_id3 =self.fiscal_emp_id4 = emps


    note_fiscal_emp = fields.Text('Note' ,default="""
                1. Numero d'ordre
                2. Noms, Prenoms qualité ou emploi et adresse des personnes rétribuées
                3. Situation de famille au 1er janvier
                4. Nombre de personnes à charge au 1er janvier .
                5. Date (MODIFICATIONS intervenant dans la situation de famille)
                6. Nature (MODIFICATIONS intervenant dans la situation de famille)
                7. Condition d'emploi
                8. Montant net des sommes perçues (janvier)
                9. Retenues à la source opérées (janvier)
                10. Montant net des sommes perçues (Février)
                11. Retenues à la source opérées (Février)
                ....
                32. Montant net des sommes perçues (Retenue Forfaitaire de 15%)
                33. Retenues à la source opérées (Retenue Forfaitaire de 15%)
                34. Total
                35. Observations
                                        """
                                        )

    def print_report(self) :
        return self.env.ref('finnapps_hr_account_reports.hr_payroll_fisc').report_action(self)


class FinnHrFiscalRecapitulation(models.Model):
    _name = "finn.hr.fiscal.rec"

    mois = fields.Char('Mois')
    date_quit = fields.Date('Date de la quittance')
    somme_traitement = fields.Float('Somme traitement')
    fiscal_id = fields.Many2one('finn.hr.fiscal')
    somme_pensions = fields.Float('Somme pensions ')
    

    retenu_traitement = fields.Float('Retenu traitement')


    retenu_pensions = fields.Float('Retenu pensions')


class FinnHrFiscalDroit(models.Model):
    _name = "finn.hr.fiscal.droit"

    nature_impo = fields.Char('Nat Imp')
    fiscal_id = fields.Many2one('finn.hr.fiscal')
    somme_paye = fields.Float('Sum Paye')
    somme_allouee = fields.Float('Sum allouée')
    salaire_impo = fields.Float('Sal Imp')
    pourboire = fields.Float('Prb')
    montant_1 = fields.Float('Net')
    montant_2 = fields.Float('Sum Dues')
    montant_3 = fields.Float('Sum Versé')
    montant_4 = fields.Float('Reste')

class FinnHrFiscalEmp(models.Model):
    _name = "finn.hr.fiscal.emp"

    origin_num = fields.Integer('N°')
    employee_id = fields.Many2one('hr.employee','Employé')
    situation = fields.Selection(string="Situation familliale", selection=[('single','C'),
                                                        ('married','M'),
                                                        ('divorced','D'),
                                                        ('widower','V')])
    fiscal_id = fields.Many2one('finn.hr.fiscal')
    number_dependents = fields.Integer('Nbr P')
    date = fields.Date('Date')
    nature = fields.Selection(string='Nature', selection=[('complete','C'),
                                                          ('partial','P')])
    emploi_condition = fields.Char('Emp cond')

    net_jan = fields.Float('Net Janvier')
    retenu_jan = fields.Float('Retenu Janvier')

    net_fev = fields.Float('Net Février')
    retenu_fev = fields.Float('Retenu Février')

    net_mars = fields.Float('Net Mars')
    retenu_mars = fields.Float('Retenu Mars')

    net_avril = fields.Float('Net Avril')
    retenu_avril = fields.Float('Retenu Avril')

    net_mai = fields.Float('Net Mai')
    retenu_mai = fields.Float('Retenu Mai')

    net_juin = fields.Float('Net Juin')
    retenu_juin = fields.Float('Retenu Juin')

    net_juil = fields.Float('Net Juillet')
    retenu_juil = fields.Float('Retenu Juillet')

    net_aout = fields.Float('Net Âout')
    retenu_aout = fields.Float('Retenu Âout')

    net_sep = fields.Float('Net Septmbre')
    retenu_sep = fields.Float('Retenu Septmbre')

    net_oct = fields.Float('Net Octobre')
    retenu_oct = fields.Float('Retenu Octobre')

    net_nov = fields.Float('Net Novembre')
    retenu_nov = fields.Float('Retenu Novembre')

    net_dec = fields.Float('Net Décembre')
    retenu_dec = fields.Float('Retenu Décembre')

    net_15 = fields.Float('Net 15')
    retenu_15 = fields.Float('Retenu 15')

    total = fields.Float('Total')

    observations = fields.Char('Observations')