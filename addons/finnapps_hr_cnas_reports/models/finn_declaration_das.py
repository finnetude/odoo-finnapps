from datetime import datetime, date ,timedelta
import os, inspect, base64
from odoo.exceptions import ValidationError

import logging as log

from odoo import models, fields, api

class FinnDeclarationDas(models.Model):
    _name = "finn.declaration.das"
    _description = 'Déclaration annuelle des salariés'

    name = fields.Char('Nom',compute="get_name")
    company_id = fields.Many2one('res.company', readonly=True ,string ='Société', default=lambda self: self.env.company)
    periode = fields.Char('Période', default=datetime.now().year)
    declaration_das_line_ids = fields.One2many('finn.declaration.das.line','declaration_das_id', 'Ligne de déclaration annuelle des salariés',relation="das_lines1")
    declaration_das_line2_ids = fields.One2many('finn.declaration.das.line','declaration_das_id', 'Ligne de déclaration annuelle des salariés',relation="das_lines2")
    declaration_das_line3_ids = fields.One2many('finn.declaration.das.line','declaration_das_id', 'Ligne de déclaration annuelle des salariés',relation="das_lines3")
    creation_date = fields.Date('Date de création', default = date.today())
    note = fields.Text('Note')
    agency_id = fields.Many2one(
        'res.partner',
        string='Agence',
        domain="[('is_cnas_agency', '=', True)]"
    )

    payment_center_id = fields.Many2one(
        'res.partner', 
        string='Centre de paiement',
        domain="[('parent_id', '=', agency_id),('is_payment_center', '=', True)]"
    )
    rtf_type_declaration = fields.Selection(
        [('normal', 'Normal'),
         ('regulation', 'Régulation'),
         ('additoinal', 'Complémentaire')],
        string="Type de déclaration",
        default="normal"
        )

    effect_employees = fields.Integer('Nombre d\'employé effectif' ,compute="_compute_employees_effectif")

    @api.depends('declaration_das_line_ids')
    def _compute_employees_effectif(self):
        self.effect_employees = len(self.declaration_das_line_ids)


    
    @api.onchange('agency_id')
    def onchange_payment_center(self):
        self.payment_center_id = False
 
    def get_name(self):
        """ This method used to customize display name of the record """
        result = []
        for record in self:
            if record.periode:
                rec_name = "%s" % ("Déclaration annuelle des salariés /" + record.periode)
                result.append((record.id, rec_name))
        return result


    @api.depends('periode')
    def get_name(self):
        """ This method used to customize display name of the record """
        result = ''
        self.name = 'New'
        for record in self:
            if record.periode:
                result = "%s" % ("Déclaration annuelle des salariés /" + record.periode)
        record.name = result

    

    def generate_company_file(self):

        def give_char(char ,taille):
            if len(char) < taille:
                i = taille - len(char)
                char += i * ' '
            return char

        # Caractère interdit pour le code d'adhérant
        code_adherant = self.agency_id.code_adherant
        characters = "'!\?/"
        for x in range(len(characters)):
            if code_adherant:
                code_adherant = code_adherant.replace(characters[x],"")

        file_name = "D" + str(self.periode)[-2:] + "E" + code_adherant + ".txt"
        path = "/var/lib/odoo/" + file_name

        val = ""
        # Code d'adhérant (taille = 10)
        val += code_adherant

        # Type de déclaration (taille = 1)
        if self.rtf_type_declaration == "normal":
            val += 'N'
        if self.rtf_type_declaration == "regulation":
            val += 'R'
        if self.rtf_type_declaration == "additoinal":
            val += 'C'

        # Période (taille = 4)
        val += str(self.periode)

        # Code de l'agence (taille = 5)
        val += str(self.agency_id.agency_code)

        # Code de forme juridique (taille = 5)
        forme_juridique = self.company_id.forme_juridique.code.lower()
        val += give_char(forme_juridique, 5)

        # Nom de la société (taille = 25)
        name = str(self.company_id.name)
        val += give_char(name, 25)

        # Nom du code d'activité (taille = 30)
        for ac in self.company_id.partner_id.activity_code_id:
            if ac.is_principal == True:
                activity_code = str(ac.name.upper())
                val += give_char(activity_code, 30)

        # Adresse 1 + adresse 2 (taille = 40)
        street = str(self.company_id.street) + ' ' + str(self.company_id.street2)
        val += give_char(street, 40)

        # ville (taille = 11)
        city = str(self.company_id.city)
        val += give_char(city, 11)

        somme1 = somme2 = somme3 = somme4 = annual_somme =  0
        for line in self.declaration_das_line_ids :
            somme1 += line.first_trimester_amount
            somme2 += line.second_trimester_amount
            somme3 += line.third_trimester_amount
            somme4 += line.fourth_trimester_amount
            annual_somme += line.annual_amount

        # Montant trimestre 1 (taille = 16)
        if somme1 == 0:
            amount_1 = "0"
        else:
            amount_1 = str("{:.2f}".format(somme1)).replace('.',"")
        val += give_char(amount_1, 16)

        # Montant trimestre 2 (taille = 16)
        if somme2 == 0:
            amount_2 = "0"
        else:
            amount_2 = str("{:.2f}".format(somme2)).replace('.',"")
        val += give_char(amount_2, 16)

        # Montant trimestre 3 (taille = 16)
        if somme3 == 0:
            amount_3 = "0"
        else:
            amount_3 = str("{:.2f}".format(somme3)).replace('.',"")
        val += give_char(amount_3, 16)

        # Montant trimestre 4 (taille = 16)
        if somme4 == 0:
            amount_4 = "0"
        else:
            amount_4 = str("{:.2f}".format(somme4)).replace('.',"")
        val += give_char(amount_4, 16)

        # Montant annuel  (taille = 1
        if annual_somme == 0:
            annual_amount = "0"
        else:
            annual_amount = str("{:.2f}".format(annual_somme)).replace('.',"")
        val += give_char(annual_amount, 16)

        # Nombre de travailleur (taille = 1)
        val += str(self.effect_employees)

        # Open a file for writing
        with open(path, "w") as f:
            # Write the row to the file
            f.write(val)

        binary_file = None
        with open(path, "rb") as f:
            binary_file = base64.b64encode(f.read())

        attachment = self.env['ir.attachment'].sudo().search([('name','=', file_name)],limit=1)
        if not attachment: 
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'res_model': 'finn.declaration.das',
                'datas' : binary_file,
                'type': 'binary',
                })
        else :
            attachment.sudo().write({'datas': binary_file})

        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_company_file?filename=%s'%(file_name),
             'target': 'self',
        }






    def generate_employee_file(self):

        action = self.env.ref('finnapps_hr_cnas_reports.action_hr_employee_list').read()[0]

        emp = self.declaration_das_line_ids.mapped('employee_id')
  
        action['context'] = {
            'default_employee_ids': emp.ids,
            'default_das_id': self.id,
            }

        return action

    def print_report(self):
        return self.env.ref('finnapps_hr_cnas_reports.declaration_das_repport').report_action(self)

    def calcule_lines(self):

        line = self.env['finn.hr.payslip.line']
        worked = self.env['finn.hr.payslip.worked_days']

        # Delete the lines ########################################################
        self.declaration_das_line_ids.unlink()
        self.declaration_das_line2_ids.unlink()
        self.declaration_das_line3_ids.unlink()

        # Get the contracts in the periode ####################

        contracts = self.env['hr.contract'].search([('struct_id.code','not in',['STCH','STCJ']),
                                                    ('date_start','<=',date(year= int(self.periode), month= 12, day= 31)),
                                                    '|',('date_end','>=',date(year= int(self.periode), month= 1, day= 1)),
                                                    ('date_end','=',False)])


        employees = self.env['hr.employee'].search(['|',('active','=',True),('active','=',False),
                                                    ('contract_ids','in', contracts.ids),
                                                    ('payment_center_id','=', self.payment_center_id.id),])


        payslips = self.env['finn.hr.payslip'].search([('employee_id','in', employees.ids),
                                                  ('company_id','=',self.company_id.id),
                                                  ('date_from','<=',date(year= int(self.periode), month= 12, day= 31)),
                                                  ('date_to','>=',date(year= int(self.periode), month= 1, day= 1)),
                                                  ('employee_id.payment_center_id','=', self.payment_center_id.id)])
        # Trimestre ###########
        t1 = [1,2,3]
        t2 = [4,5,6]
        t3 = [7,8,9]
        t4 = [10,11,12]


        values = {}

        # Go throught all the payslips
        for payslip in payslips:


            amount = line.search([('id','in',payslip.line_ids.ids),
                    ('code','=','NET')]).total
            nbr_jr = worked.search([('id','in',payslip.worked_days_line_ids.ids),
                    ('code','=','WORK100')]).number_of_days
            nbr_jr_cp = worked.search([('id','in',payslip.worked_days_line_ids.ids),
                    ('code','=','CP')]).number_of_days

            date_start = self.env['hr.contract'].search(
                [('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'open')],limit=1).date_start
            date_end = self.env['hr.contract'].search(
                [('employee_id', '=', payslip.employee_id.id)],order="date_start desc" ,limit=1).date_end
            if payslip.employee_id not in values.keys():
                values.update({payslip.employee_id :
                {
                    'name': payslip.employee_id.ssnid,
                    'employee_id': payslip.employee_id.id,
                    'company_id': self.company_id.id,
                    'input_date': date_start,
                    'output_date': date_end, 
                    'first_trimester_amount': 0,
                    'first_trimester_number_day': 0,
                    'second_trimester_amount': 0,
                    'second_trimester_number_day': 0,
                    'third_trimester_amount': 0,
                    'third_trimester_number_day': 0,
                    'fourth_trimester_amount': 0,
                    'fourth_trimester_number_day': 0,
                    'annual_amount': 0,
                    'total_number_day': 0,
                } 
                    })

            else :
                if not values[payslip.employee_id]['input_date'] or payslip.contract_id.date_start < values[payslip.employee_id]['input_date']:
                    values[payslip.employee_id].update({'input_date': payslip.contract_id.date_start })

                if not values[payslip.employee_id]['output_date'] or payslip.contract_id.date_end > values[payslip.employee_id]['output_date']:
                    values[payslip.employee_id].update({'output_date': payslip.contract_id.date_end })


            if payslip.date_from.month in t1:
                values[payslip.employee_id].update({
                    'first_trimester_amount': values[payslip.employee_id]['first_trimester_amount'] + amount,
                    'first_trimester_number_day': values[payslip.employee_id]['first_trimester_number_day'] + nbr_jr + nbr_jr_cp,
                    })
            elif payslip.date_from.month in t2:
                values[payslip.employee_id].update({
                    'second_trimester_amount': values[payslip.employee_id]['second_trimester_amount'] + amount,
                    'second_trimester_number_day': values[payslip.employee_id]['second_trimester_number_day'] + nbr_jr + nbr_jr_cp,
                    })
            elif payslip.date_from.month in t3:
                values[payslip.employee_id].update({
                    'third_trimester_amount': values[payslip.employee_id]['third_trimester_amount'] + amount,
                    'third_trimester_number_day': values[payslip.employee_id]['third_trimester_number_day'] + nbr_jr + nbr_jr_cp,
                    })
            else :
                values[payslip.employee_id].update({
                    'fourth_trimester_amount': values[payslip.employee_id]['fourth_trimester_amount'] + amount,
                    'fourth_trimester_number_day': values[payslip.employee_id]['fourth_trimester_number_day'] + nbr_jr + nbr_jr_cp,
                    })

            values[payslip.employee_id].update({
                'annual_amount': values[payslip.employee_id]['annual_amount'] + amount,
                'total_number_day': values[payslip.employee_id]['total_number_day'] + nbr_jr + nbr_jr_cp

                })

        for val in values :

            self.declaration_das_line_ids += self.env['finn.declaration.das.line'].create(values[val])
        self.declaration_das_line3_ids = self.declaration_das_line2_ids = self.declaration_das_line_ids

    def generate_rtf(self):

        table_lines = []

        #delete old attachment recs if existe
        old_recs = self.env['ir.attachment'].search([('name', '=', 'Déclaration annuelle des salariés.rtf')])
        if old_recs:
            old_recs.unlink()

        total = self.declaration_das_line_ids
        first_2nd_trim = self.declaration_das_line2_ids
        thrd_4th_trim = self.declaration_das_line3_ids

        #the das lines needs to be already calculated
        if not(total or first_2nd_trim or thrd_4th_trim):
            raise models.ValidationError("Calculé DAS.")

        #prepare the report table lines data 
        for i in range(len(total)):
            table_lines.append([
                total[i].employee_id.ssnid if total[i].employee_id.ssnid else "____",
                total[i].employee_id.birthday.strftime("%d/%m/%Y") if total[i].employee_id.birthday else "__/__/____",
                "     " + total[i].employee_id.name,
                first_2nd_trim[i].first_trimester_number_day,
                "J" if first_2nd_trim[i].first_trimester_number_day != 0 else "M",
                first_2nd_trim[i].first_trimester_amount,
                first_2nd_trim[i].second_trimester_number_day,
                "J" if first_2nd_trim[i].second_trimester_number_day != 0 else "M",
                first_2nd_trim[i].second_trimester_amount,
                thrd_4th_trim[i].third_trimester_number_day,
                "J" if thrd_4th_trim[i].third_trimester_number_day != 0 else "M",
                thrd_4th_trim[i].third_trimester_amount,
                thrd_4th_trim[i].fourth_trimester_number_day,
                "J" if thrd_4th_trim[i].fourth_trimester_number_day != 0 else "M",
                thrd_4th_trim[i].fourth_trimester_amount,
                total[i].annual_amount,
                total[i].input_date.strftime("%d/%m/%Y") if total[i].input_date else "__/__/____",
                total[i].output_date.strftime("%d/%m/%Y") if total[i].output_date else "__/__/____",
            ])

        #prepare the company/cnas data
        search_text = [
            'n_assure', 'date_ness', 'nom_prenom','dur1',
            'tp1','month_tr1','dur2','tp2','month_tr2',
            'dur3','tp3','month_tr3','dur4','tp4',
            'month_tr4', 'month_trg','date_entr','date_sort']
        fixed_search_text = [
            'code_dad', 'jurid_code', 'comp_name','form_juride_name',
            'adress_comp', 'exer_year','declat_type',
        ]

        if self.rtf_type_declaration == 'normal':
            type_declar = "N"
        elif self.rtf_type_declaration == 'regulation':
            type_declar = "R"
        elif self.rtf_type_declaration == 'additoinal':
            type_declar = "C"
        else:
            type_declar = "____"

        fixed_replace_text = [
            self.agency_id.code_adherant if self.agency_id.code_adherant else "____",
            self.company_id.forme_juridique.code if self.company_id.forme_juridique.code else "",
            self.company_id.name, self.company_id.activite if self.company_id.activite else "",
            self.company_id.street if self.company_id.street else "Adress", int(self.periode), 
            type_declar
        ]
        
        #get the resources files path
        path = os.path.expanduser(self.get_txt_path_table())
        path_temp = os.path.expanduser(self.get_txt_path_template())

        with open(path, 'r') as  file:
            next_line = file.read()

        with open(path, 'r') as file:
            data = file.read()

        #replacing palce holder keywords in the table line template with it corresponding data
        for i in range(len(table_lines)):
            
            for n in range(len(search_text)):
                data = data.replace(search_text[n], str(table_lines[i][n]))
            if table_lines[i] != table_lines[-1]:
                data = data.replace('table_data_lines', next_line)
        data = data.replace('table_data_lines', "")
        #the result after that is the table line hangig out there on their own
        
        #geting company/cnas data and the lines in the general template
        with open(path_temp, 'r') as file:
            fixed = file.read()

        for i in range(len(fixed_search_text)):
            if "é" in str(fixed_replace_text[i]):
                fixed_replace_text[i] = fixed_replace_text[i].replace("é", "\\'e9")
            if "è" in str(fixed_replace_text[i]):
                fixed_replace_text[i] = fixed_replace_text[i].replace("è", "\\'e8")
            if "à" in str(fixed_replace_text[i]):
                fixed_replace_text[i] = fixed_replace_text[i].replace("à", " \\'e0 ")
            if "°" in str(fixed_replace_text[i]):
                fixed_replace_text[i] = fixed_replace_text[i].replace("°", "\\'b0")

            fixed = fixed.replace(fixed_search_text[i], str(fixed_replace_text[i]))
        
        #geting the 4 trimesters numbers
        calcs_search_text = [
            'tot_trim1', 'tot_trim2', 'tot_trim3','tot_trim4',
            'annual_bal', 'emp_effect'
        ]

        total_1=0
        total_2=0
        total_3=0
        total_4=0
        annual_bal=0
        for emp in self.declaration_das_line_ids:
            total_1 = total_1 + emp.first_trimester_amount
            total_2 = total_2 + emp.second_trimester_amount
            total_3 = total_3 + emp.third_trimester_amount
            total_4 = total_4 + emp.fourth_trimester_amount
            annual_bal = annual_bal + emp.annual_amount
        
        calcs_replace_text = [
            f'{total_1:,.2f}'.replace(',', ' '), f'{total_2:,.2f}'.replace(',', ' '),
            f'{total_3:,.2f}'.replace(',', ' '), f'{total_4:,.2f}'.replace(',', ' '),
            f'{annual_bal:,.2f}'.replace(',', ' '), len(self.declaration_das_line_ids)
        ]

        for i in range(len(calcs_search_text)):
            fixed = fixed.replace(calcs_search_text[i], str(calcs_replace_text[i]))
        fixed = fixed.replace('date_release', str(datetime.today().strftime('%m/%d/%Y')))

        fixed = fixed.replace('table_data_lines', data)

        #creating the rtf report    
        with open("/var/lib/odoo/Déclaration annuelle des salariés.rtf", "w", newline='') as file:

            file.write(fixed)

        #encoding the file in a way odoo can store it as attachment in the ir.attachments model
        binary_file = None

        with open("/var/lib/odoo/Déclaration annuelle des salariés.rtf", "rb") as f:
            binary_file = base64.b64encode(f.read())
        
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.env['ir.attachment']
        # create attachment
        attachment_id = attachment_obj.create(
            {'name': "Déclaration annuelle des salariés.rtf", 'type': 'binary', 'datas': binary_file})
        #prepare the download link
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'

        #returning the url as url action and downloading the file
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    #this 2 methods are meant to get the absolute resources files path
    def get_txt_path_table(slef):
        directory_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        directory_path = directory_path.replace('models', 'resources')
        return os.path.join(directory_path, 'table.txt')

    def get_txt_path_template(slef):
        directory_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        directory_path = directory_path.replace('models', 'resources')
        return os.path.join(directory_path, 'general_temp_copy.rtf')



class FinnDeclarationDasLines(models.Model):
    _name = "finn.declaration.das.line"
    _description = 'Ligne de déclaration annuelle des salariés'

    employee_id = fields.Many2one('hr.employee','Nom & Prénom')

    name = fields.Char('N° SS', compute="_compute_ss",store=True)
    company_id = fields.Many2one('res.company','Société',default=lambda self: self.env.company)
    annual_amount = fields.Float('Montant annuel')
    total_number_day = fields.Integer('Nombre de jour total')
    input_date = fields.Date('Date d\'entré')
    output_date = fields.Date('Date de sortie')

    first_trimester_amount = fields.Float('Montant du trimestre 1')
    first_trimester_number_day = fields.Integer('Nbr jour pendant T1')

    second_trimester_amount = fields.Float('Montant du trimestre 2')
    second_trimester_number_day = fields.Integer('Nbr jour pendant T2')

    third_trimester_amount = fields.Float('Montant du trimestre 3')
    third_trimester_number_day = fields.Integer('Nbr jour pendant T3')

    fourth_trimester_amount = fields.Float('Montant du trimestre 4')
    fourth_trimester_number_day = fields.Integer('Nbr jour pendant T4')

    declaration_das_id = fields.Many2one('finn.declaration.das')
    payment_center_line_id = fields.Many2one(related="declaration_das_id.payment_center_id")

    @api.depends('employee_id')
    def _compute_ss(self):
        for obj in self:
            obj.name = obj.employee_id.ssnid


