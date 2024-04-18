from odoo import models, fields
import base64


class FinnEmployeeList(models.TransientModel):

    _name = 'finn.employee.list'
    _description= "Liste des employés"


    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel2',  string='Liste des employés')
    das_id = fields.Many2one('finn.declaration.das')


    def generate(self):
        file_name = "D" + str(self.das_id.periode)[-2:] + "S" + self.das_id.agency_id.code_adherant + ".txt"
        path = "/var/lib/odoo/" + file_name
        self.generate_file(path)


        binary_file = None
        file = open(path, 'r')

        
        with open(path, "rb") as f:
            binary_file = base64.b64encode(f.read())



        attachment = self.env['ir.attachment'].sudo().search([('name','=', file_name)],limit=1)
       
        if not attachment: 
            
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'res_model': 'declaration.das',
                'datas' : binary_file,
                'type': 'binary',
                })
        else :
            attachment.sudo().write({'datas': binary_file})


        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_employee_file?filename=%s'%(file_name),
             'target': 'self',
        }




    def generate_file(self, path):

        def give_char(char ,taille):
            if len(char) < taille:
                i = taille - len(char)
                char += i * ' '
            return char

        commun = ""
        # Code d'adhérant (taille = 10)
        code_adherant = self.das_id.agency_id.code_adherant
        commun += give_char(code_adherant, 10)

        # Période (taille = 4)
        periode = str(self.das_id.periode)
        commun += give_char(periode, 4)

        i = 1
        vals = []
        for line in self.das_id.declaration_das_line_ids :
            val = commun

            # Numéro de ligne (taille = 6)
            val += give_char(str(i), 6)

            # Numéro de sécurité sociale (taille = 12)
            n_ss = str(line.name)
            val += give_char(n_ss, 12)

            # Nom (taille = 25)
            nom = str(line.employee_id.family_name.upper())
            val += give_char(nom, 25)

            # Prénom (taille = 25)
            prenom = str(line.employee_id.surname.upper())
            val += give_char(prenom, 25)

            # Date de naissence (taille = 8)
            if line.employee_id.birthday:
                day = str(line.employee_id.birthday.day)
                if len(day) == 1:
                    day = '0' + day
                month = str(line.employee_id.birthday.month)
                if len(month) == 1:
                    month = '0' + month
                birthday = day + month + str(line.employee_id.birthday.year)
            else:
                birthday = "00000000"
            val += give_char(birthday, 8)

            # Nombre de jour travaillé T1 (avec J) (taille = 3)
            jour_t1 = str(line.first_trimester_number_day)
            val += give_char(jour_t1, 3) + 'J'

            # Montant du T1 (taille = 10)
            amout_t1 = str("{:.2f}".format(line.first_trimester_amount)).replace('.',"") if line.first_trimester_amount else "0"
            val += give_char(amout_t1, 10)

            # Nombre de jour travaillé T2 (avec J) (taille = 3)
            jour_t2 = str(line.second_trimester_number_day)
            val += give_char(jour_t2, 3) + 'J'

            # Montant du T2 (taille = 10)
            amout_t2 = str("{:.2f}".format(line.second_trimester_amount)).replace('.',"") if line.second_trimester_amount else "0"
            val += give_char(amout_t2, 10)

            # Nombre de jour travaillé T3 (avec J) (taille = 3)
            jour_t3 = str(line.third_trimester_number_day)
            val += give_char(jour_t3, 3) + 'J'

            # Montant du T3 (taille = 10)
            amout_t3 = str("{:.2f}".format(line.third_trimester_amount)).replace('.',"") if line.third_trimester_amount else "0"
            val += give_char(amout_t3, 10)

            # Nombre de jour travaillé T4 (avec J) (taille = 3)
            jour_t1 = str(line.fourth_trimester_number_day)
            val += give_char(jour_t1, 3) + 'J'
            
            # Montant du T4 (taille = 10)
            amout_t4 = str("{:.2f}".format(line.fourth_trimester_amount)).replace('.',"") if line.fourth_trimester_amount else "0"
            val += give_char(amout_t4, 10)

            # Montant annuel (taille = 12)
            annual_amount = str("{:.2f}".format(line.annual_amount)).replace('.',"")
            val += give_char(annual_amount, 12)

            # Date de début (taille = 8)
            day = str(line.input_date.day)
            if len(day) == 1:
                day = '0' + day
            month = str(line.input_date.month) 
            if len(month) == 1:
                month = '0' + month
            date_debut = day + month + str(line.input_date.year)
            val += give_char(date_debut, 8)

            # Date de fin (taille = 8)
            if line.output_date:
                day = str(line.output_date.day)
                if len(day) == 1:
                    day = '0' + day
                month = str(line.output_date.month)
                if len(month) == 1:
                    month = '0' + month
                date_fin = day + month + str(line.output_date.year)
            else:
                date_fin = ""
            val += give_char(date_fin, 8)

            # Fin de ligne (taille = 20)
            val += give_char("", 20)
            val += "0"
            i += 1
            vals.append(val)

        # Open a file for writing
        file = open(path, "w", newline='')
        # Iterate over the rows of the sheet
        for row in vals:
            # Write the row to the file
            file.write(row + "\n")

        file.close()

