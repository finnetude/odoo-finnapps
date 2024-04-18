from odoo import models, fields, api, _
import datetime
from calendar import monthrange
from collections import OrderedDict
import base64
import xlsxwriter
import calendar

class FinnHrPayrollBook(models.Model):
    _name = "finn.hr.payroll.book"
    _description = "Livre de paie"
    
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)

    name = fields.Char('Nom', compute="_compute_name")
    year = fields.Char('Année',default=datetime.datetime.now().year)
    month = fields.Selection([('1','Janvier'),('2','Février'),('3','Mars'),
            ('4','Avril'),('5','Mai'),('6','Juin'),
            ('7','Juillet'),('8','Août'),('9','Septembre'),
            ('10','Octobre'),('11','Novembre'),('12','Décembre'),
        ],'Mois',default=str(datetime.datetime.now().month))
    
    note = fields.Text('Note')
    
    payslip_ids = fields.Many2many('finn.hr.payslip',relation ="rel_payslip", readonly="1")
    pyaslip_pres_ids = fields.Many2many('finn.hr.payslip',relation ="rel_payslip_pres", readonly="1")

    payslip_details_ids = fields.Many2many('finn.hr.payslip.line', relation ="rel_payslip_details", readonly="1")
    prestation_details_ids = fields.Many2many('finn.hr.payslip.line', relation ="rel_prestation_details", readonly="1")

    payslip_details_total_ids = fields.Many2many('finn.hr.payroll.book.total',relation ="rel_payslip_details_total", readonly="1",default_order='sequence, asc')
    prestation_details_total_ids = fields.Many2many('finn.hr.payroll.book.total', relation ="rel_prestation_details_total", readonly="1")

    


    @api.onchange('month','year')
    def _compute_name(self):
        months = {'1':'Janvier','2':'Février','3':'Mars','4':'Avril',
        '5':'Mai','6':'Juin','7':'Juillet','8':'Août','9':'Septembre',
        '10':'Octobre','11':'Novembre','12':'Décembre', ' ': ' '}
        for record in self:

            record.name = "Livre de paie" + " " +months[str(record.month if record.month else " ")] + " " + str(record.year if record.year else " ")
    
    def generate_date(self, int_year, int_month):
        var_day = monthrange(int_year, int_month)[1]
        var_premier_jour = datetime.date(int_year, int_month, 1) # Premier jour du mois
        var_dernier_jour = datetime.date(int_year, int_month, var_day) # Dernier jour du mois
        return var_premier_jour, var_dernier_jour

    def prepare_payslip(self, domain, var_premier_jour, var_dernier_jour):
        contracts = self.env['hr.contract'].search(domain)
        payslip_ids = self.env['finn.hr.payslip'].search([('contract_id','in', contracts.ids),
            ('date_from','<=', var_dernier_jour),('date_to','>=', var_premier_jour)])
        return payslip_ids

    def prepare_details_total(self, details_total):
        liste_code = []
        liste_total = []
        for line in details_total:
            if line.total == 0.0 and line.code != 'IRG' or line.category_id.code in ['BASIC','GROSS','HJ','COEFF'] or line.code in ['MC']:
                continue
            if line.code not in liste_code:
                liste_total.append({'name':line.name,'code':line.code,'total':line.total,'sequence':line.sequence})
                liste_code.append(line.code)
                continue
            if line.code in liste_code:
                for code in liste_total:
                    if line.code == code['code']:
                        code['total'] += line.total
        details_total_ids = []
        for total in liste_total:
            details_total_ids.append((0,0,total))
        
        return details_total_ids

    def payroll_book_lines(self):
        self.write({
            'payslip_ids': False,
            'pyaslip_pres_ids': False,
            'payslip_details_ids': False,
            'prestation_details_ids': False})
        self.payslip_details_total_ids.unlink()
        self.prestation_details_total_ids.unlink()
        payslip_details_ids = False
        prestation_details_ids = False
        payslip_details_total_ids = False
        prestation_details_total_ids = False

        var_premier_jour, var_dernier_jour = self.generate_date(int(self.year), int(self.month))

        domain_emp = [('structure_type_id.name','not in',['Consultant','Stagiaire'])]
        domain_consult  = [('structure_type_id.name','=','Consultant')]

        payslip_ids = self.prepare_payslip(domain_emp, var_premier_jour, var_dernier_jour)
        pyaslip_pres_ids = self.prepare_payslip(domain_consult, var_premier_jour, var_dernier_jour)
        

        if payslip_ids:
            payslip_details_ids = payslip_ids.line_ids
        if pyaslip_pres_ids:
            prestation_details_ids = pyaslip_pres_ids.line_ids

        if payslip_details_ids:
            payslip_details_total_ids = self.prepare_details_total(payslip_details_ids)
        if prestation_details_ids:
            prestation_details_total_ids = self.prepare_details_total(prestation_details_ids)
        

        self.write({
            'payslip_ids': payslip_ids or False,
            'pyaslip_pres_ids': pyaslip_pres_ids or False,
            'payslip_details_ids': payslip_details_ids or False,
            'prestation_details_ids': prestation_details_ids or False,
            'payslip_details_total_ids': payslip_details_total_ids or False,
            'prestation_details_total_ids': prestation_details_total_ids or False,
            })
        
    def get_datas(self):
        res = []
        
        cols = self.payslip_details_total_ids.mapped("code")
        for emp in self.payslip_ids:
            emps = []
            for code in cols:
                res_cod = emp.line_ids.filtered(lambda m: m.code == code)
                if res_cod:
                    emps.append(res_cod.total)
                else:
                    emps.append(0.00)
            res.append(emps)

        return res
        
    def print_payroll(self):
        return self.env.ref("finnapps_hr_account_reports.report_hr_payroll_book_payrol").report_action(self)
             
    def print_payroll_in_excel(self):
    
        report_name = 'finnapps_hr_account_reports.report_hr_payroll_book_payrol'
        
        file_name = str('/var/lib/odoo/{}.xlsx'.format(report_name))
        workbook = xlsxwriter.Workbook(file_name)

      

        sheet = workbook.add_worksheet(self.company_id.name)
        format_table_body = workbook.add_format()
        format_table_body.set_align("center")
        format_table_body.set_valign("vjustify")
        format_table_body.set_border(1)
        format_table_body.set_bold(False)
        format_table_body.set_font_size(10)
        format_table_body.set_border_color("#c1c3c1")
        format_table_body.set_bg_color("#EFEFEF")

        format_table_body1 = workbook.add_format()
        format_table_body1.set_align("center")
        format_table_body1.set_valign("vjustify")
        format_table_body1.set_border(1)
        format_table_body1.set_bold(False)
        format_table_body1.set_font_size(10)
        format_table_body1.set_border_color("#c1c3c1")
        format_table_body1.set_bg_color("#FFFFFF")

        format_table_header = workbook.add_format()
        format_table_header.set_align("center")
        format_table_header.set_valign("vjustify")
        format_table_header.set_border(1)
        format_table_header.set_bold(True)
        format_table_header.set_font_size(12)
        format_table_header.set_bg_color("#EFEFEF")
        format_table_header.set_border_color("#cbcbcb")
        format_table_header.set_font_color("black")

        format_table_footer = workbook.add_format()
        format_table_footer.set_align("center")
        format_table_footer.set_valign("vjustify")
        format_table_footer.set_border(1)
        format_table_footer.set_bold(True)
        format_table_footer.set_font_size(10.5)
        format_table_footer.set_bg_color("#EFEFEF")
        format_table_footer.set_border_color("#cbcbcb")
        format_table_footer.set_font_color("black")

        format_titre = workbook.add_format()
        format_titre.set_align("center")
        format_titre.set_valign("vcenter")
        format_titre.set_border(0)
        format_titre.set_bold(True)
        format_titre.set_font_size(18)

        format_header = workbook.add_format()
        format_header.set_align("center")
        format_header.set_valign("vcenter")
        format_header.set_border(0)
        format_header.set_bold(True)
        format_header.set_font_size(11)
        
        sheet.set_landscape()
        sheet.set_paper(9) # 9 = A4 format page
        sheet.set_footer('&CPage &P / &N')

        sheet.merge_range('A1:D2', "", format_header)
        sheet.write("A1", str(self.company_id.name), format_header)
        sheet.merge_range('B3:M5', "", format_titre)
        sheet.write("B3", str("Livre de Paie"), format_titre)
        sheet.merge_range('E6:J6', "", format_header)
        sheet.write("E6", str( "Pour "+str(self.month)+ " " + str(self.year) ), format_header)

        alphabets = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','V','W','X','Y','Z']
        
        length_salary = len(self.payslip_details_total_ids)

        length = 2 + length_salary
        header = [u"Nom /Fonction", "Nbr"]

        for rule in self.payslip_details_total_ids:
            header.append("{}".format(rule.name))

        sheet.set_column('A:A', 18)
        pos = ["A"]
        for i in range(1,length):
            para = str(alphabets[i])+':'+str(alphabets[i])
            
            sheet.set_column(str(alphabets[i])+':'+str(alphabets[i]), 30)
            pos.append(alphabets[i])

        curr_line = 7
        
        sheet.set_row(curr_line, 30)
        for i, h in enumerate(header):
            sheet.write(pos[i] + str(curr_line+1), h, format_table_header)
        curr_line += 1


        total1 = 0
        res = self.get_datas()
        index = 0

        for line in self.payslip_ids:
            
            
            sheet.set_row(curr_line, 30)
           
            _line = [
                str(line.employee_id.name) +"\n" + str(line.contract_id.job_id.name) , 
                sum(line.worked_days_line_ids.filtered(lambda x: x.code in ['WORK100', 'CP']).mapped('number_of_days')) ,
           
            ]
          
            for r in res[index]:
                
                _line.append('{0:,.2f}'.format(abs(r)).replace(',', ' ') )

            index += 1
                


            for i, l in enumerate(_line):
                if curr_line % 2:
                    sheet.write(pos[i] + str(curr_line+1), str(l), format_table_body)
                else:
                    sheet.write(pos[i] + str(curr_line+1), str(l), format_table_body1)
            curr_line += 1


        sheet.set_row(curr_line, 40)
        total_line = [
                    "TOTAUX : ",
                    "",               
                ]
      
        for t in self.payslip_details_total_ids:
            
            total_line.append('{0:,.2f}'.format(abs(t.total)).replace(',', ' '))
 
        for i, tl in enumerate(total_line):
            sheet.write(pos[i] + str(curr_line+1), tl, format_table_footer)
        curr_line += 1
        workbook.close()

        binary_file = None
        with open(file_name, "rb") as f:
            binary_file = base64.b64encode(f.read())

        attachment_id = self.env['ir.attachment'].create({
            'name': '{}.xlsx'.format(report_name),
            'datas': binary_file,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id,),
            'target': 'new',
        }


    #############################################################################################
    
    
    def print_service(self):
        return self.env.ref("finnapps_hr_account_reports.hr_payroll_etat_prestation_details").report_action(self)
    
    def print_excel_service_delivery(self):
    
        report_name = 'finnapps_hr_account_reports.hr_payroll_etat_prestation_details'
      
        line, total = self.get_payslip_line_etat_prestation()

        _datas =  { 'lines': line, 'total': total }

        return self.generate_fiscal_xlsx_report(_datas, report_name)
    
    def get_payslip_line_etat_prestation(self):
        employees = self.env['hr.employee']
        payslips = self.env['finn.hr.payslip']
        lines = self.env['finn.hr.payslip.line']
        worked_days = self.env['finn.hr.payslip.worked_days']
        line = []
        total = []
        domain = []
        month = ""

        months_fr = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet',
                     'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

        centers = set()
        for e in employees.search(['|',('active', '=', False),('active', '=', True)]):
            centers.add(e.address_id.name)
        centers = list(centers)

        for center in centers:
            is_empty = True
            total_retenue_ss, total_base_imposable, total_base_cotisable = (0,) * 3
            total_consultant_irg, total_salaire_net = (0,) * 2
            salaire_base_jour, salaire_base, quantity, total_salaire_base_jour, total_salaire_base = (0,) * 5 

            employee_ids = list()
            for e in employees.search(['&', '|', ('active', '=', False),('active', '=', True), '&' ,('address_id.name', '=', center),
                                       ('address_id.name', '!=', False)]):
                employee_ids.append(e.id)

            if not center:
                center = "Sans centre"
                for e in employees.search(['&', '|',('active', '=', False),('active', '=', True),('address_id', '=', False)]):
                    employee_ids.append(e.id)

            domain = [
                      ('employee_id', 'in', employee_ids),
                      ('state', 'in', ['done', 'draft']), ('credit_note', '=', False), ('refund_payslip', '=', False),
                      ('date_from', '>=', datetime.date(year=int(self.year), month=int(self.month), day=1)),
                      ('date_from', '<=', datetime.date(year=int(self.year), month=int(self.month), day=calendar.monthrange(int(self.year), int(self.month))[1]))]

            for payslip in self.pyaslip_pres_ids.search(domain):
                if payslip.contract_id. structure_type_id.name == "Consultant":
                    is_empty = False
                    month = months_fr[payslip.date_from.month - 1]
                    rubriques_imposables, rubriques_cotisables, rubriques_base = (0,) * 3
                    salaire_base_jour, salaire_base = (0,) * 2
                    salaire_net, retenue_ss, retenue_irg = (0,) * 3
                    base_imposable, base_cotisable, quantity = (0,) * 3
                    consultant_irg = 0

                    for l in lines.search([('slip_id', '=', payslip.id)]):
                        if l.code == "100":
                            salaire_base_jour = l.amount
                            salaire_base = round(l.total, 2)
                            quantity = round(l.quantity, 2)
                            total_salaire_base_jour += l.amount
                            total_salaire_base += round(l.total, 2)
                        elif l.code == "SS":
                            retenue_ss = round(l.total, 2)
                            total_retenue_ss += round(l.total, 2)
                        elif l.code == "IRGC":
                            consultant_irg = round(l.total, 2)
                            total_consultant_irg += round(l.total, 2)

                    for l in lines.search([('slip_id', '=', payslip.id),
                                           ('category_id.code', '=', 'BASIC')]):
                        rubriques_base += round(l.total, 2)
                    for l in lines.search([('slip_id', '=', payslip.id),
                                           ('category_id.code', '=', 'COT')]):
                        rubriques_cotisables += round(l.total, 2)
                    for l in lines.search([('slip_id', '=', payslip.id),
                                           ('category_id.code', '=', 'IMP')]):
                        rubriques_imposables += round(l.total, 2)
                    for l in lines.search([('slip_id', '=', payslip.id),
                                           ('category_id.code', '=', 'NET')]):
                        salaire_net += round(l.total, 2)
                        total_salaire_net += round(l.total, 2)

                    base_cotisable = rubriques_base + rubriques_cotisables
                    base_imposable = base_cotisable + rubriques_imposables - retenue_ss
                    total_base_imposable += base_imposable
                    total_base_cotisable += base_cotisable
                 

                    line.append({
                        'center': center,
                        'job_title': payslip.contract_id.job_id.name,
                        'full_name': payslip.employee_id.display_name,
                        'month': month,
                        'salaire_base': salaire_base,
                        'salaire_net': salaire_net,
                        'base_cotisable': base_cotisable,
                        'base_imposable': base_imposable,
                        'retenue_ss':   retenue_ss,
                        'consultant_irg': consultant_irg,
                    })
                   
            if not is_empty:
                total.append({
                'center': center,
                'month': month,
                'year': self.year,
                'total_salaire_base': total_salaire_base,
                'total_salaire_net': total_salaire_net,
                'total_base_cotisable': total_base_cotisable,
                'total_base_imposable': total_base_imposable,
                'total_consultant_irg': total_consultant_irg,
            })

        return line, total
    
  
    def generate_fiscal_xlsx_report(self, data, report_name):
        file_name = str('/var/lib/odoo/{}.xlsx'.format(report_name))
        workbook = xlsxwriter.Workbook(file_name)

        sheets = []
        for i in range(len(data['total'])):
            sheets.append(workbook.add_worksheet(data['total'][i]['center'][:31]))
        format_table_body = workbook.add_format()
        format_table_body.set_align("center")
        format_table_body.set_valign("vjustify")
        format_table_body.set_border(1)
        format_table_body.set_bold(False)
        format_table_body.set_font_size(10)
        format_table_body.set_border_color("#c1c3c1")
        format_table_body.set_bg_color("#EFEFEF")

        format_table_body1 = workbook.add_format()
        format_table_body1.set_align("center")
        format_table_body1.set_valign("vjustify")
        format_table_body1.set_border(1)
        format_table_body1.set_bold(False)
        format_table_body1.set_font_size(10)
        format_table_body1.set_border_color("#c1c3c1")
        format_table_body1.set_bg_color("#FFFFFF")

        format_table_header = workbook.add_format()
        format_table_header.set_align("center")
        format_table_header.set_valign("vjustify")
        format_table_header.set_border(1)
        format_table_header.set_bold(True)
        format_table_header.set_font_size(12)
        format_table_header.set_bg_color("#EFEFEF")
        format_table_header.set_border_color("#cbcbcb")
        format_table_header.set_font_color("black")

        format_table_footer = workbook.add_format()
        format_table_footer.set_align("center")
        format_table_footer.set_valign("vjustify")
        format_table_footer.set_border(1)
        format_table_footer.set_bold(True)
        format_table_footer.set_font_size(10.5)
        format_table_footer.set_bg_color("#EFEFEF")
        format_table_footer.set_border_color("#cbcbcb")
        format_table_footer.set_font_color("black")

        format_titre = workbook.add_format()
        format_titre.set_align("center")
        format_titre.set_valign("vcenter")
        format_titre.set_border(0)
        format_titre.set_bold(True)
        format_titre.set_font_size(18)

        format_header = workbook.add_format()
        format_header.set_align("center")
        format_header.set_valign("vcenter")
        format_header.set_border(0)
        format_header.set_bold(True)
        format_header.set_font_size(11)
        for s, sheet in enumerate(sheets):
            total = data['total'][s]
            sheet.set_landscape()
            sheet.set_paper(9) # 9 = A4 format page
            sheet.set_footer('&CPage &P / &N')

            sheet.merge_range('A1:D2', "", format_header)
            sheet.write("A1", str(total['center']), format_header)
            sheet.merge_range('B3:M5', "", format_titre)
            sheet.write("B3", str("Livre des prestations de service"), format_titre)
            sheet.merge_range('E6:J6', "", format_header)
            sheet.write("E6", str( "Pour "+str(total['month'])+ " " + str(total['year']) ), format_header)

            header = [u"Nom et prénom", "Poste", "Base imposable", "IRG", "Montant à payer", "Signature"]
            
            sheet.set_column('A:A', 18)
            sheet.set_column('B:B', 20)
            sheet.set_column('C:C', 10)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:E', 10)
            sheet.set_column('F:F', 10)
            pos = ["A", "B", "C", "D", "E", "F"]

            curr_line = 7

            sheet.set_row(curr_line, 30)
            for i, h in enumerate(header):
                sheet.write(pos[i] + str(curr_line+1), h, format_table_header)
            curr_line += 1
            
            for line in data['lines']:
                if total['center'] == line['center']:
                    if not line['full_name'] or len(line['full_name']) <= 13:
                        sheet.set_row(curr_line, 30)
                    elif len(line['full_name']) <= 20:
                        sheet.set_row(curr_line, 35)
                    else:
                        sheet.set_row(curr_line, 50)
                    _line = [
                        line['full_name'] if line['full_name'] else '',
                        line['job_title'] if line['job_title'] else '' , 
                        round(abs(line['base_imposable']), 2) if line['base_imposable'] else '',   
                        round(abs(line['consultant_irg']), 2) if line['consultant_irg'] else '',   
                        round(abs(line['salaire_net']), 2) if line['salaire_net'] else '',   
                        ""
                    ]
                    
                    for i, l in enumerate(_line):
                        if curr_line % 2:
                            sheet.write(pos[i] + str(curr_line+1), str(l), format_table_body)
                        else:
                            sheet.write(pos[i] + str(curr_line+1), str(l), format_table_body1)
                    curr_line += 1

            sheet.set_row(curr_line, 40)
            total_line = [
                        "TOTAUX : ",
                        "",
                        round(abs(total['total_base_imposable']), 2) if total['total_base_imposable'] else '',                    
                        round(abs(total['total_consultant_irg']), 2) if total['total_consultant_irg'] else '',                    
                        round(abs(total['total_salaire_net']), 2) if total['total_salaire_net'] else '', 
                        ""                   
                    ]
            
            for i, tl in enumerate(total_line):
                sheet.write(pos[i] + str(curr_line+1), tl, format_table_footer)
            curr_line += 1
        workbook.close()

        
        binary_file = None
        with open(file_name, "rb") as f:
            binary_file = base64.b64encode(f.read())

        attachment_id = self.env['ir.attachment'].create({
            'name': '{}.xlsx'.format(report_name),
            'datas': binary_file,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id,),
            'target': 'new',
        }
