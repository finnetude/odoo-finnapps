from odoo import models, fields, api,_
from datetime import datetime,date
import os, inspect, base64
from odoo.exceptions import ValidationError
import logging as log

class FinnTransferOrder(models.Model):
    
    _name = "finn.transfer.order"
    _description = "Ordre de virement"
    _inherit = ['mail.thread','mail.activity.mixin']



    @api.model
    def get_company_address(self):

        address_one = self.env.company.street if self.env.company.street else ' '
        address_two = self.env.company.street2 if self.env.company.street2 else ' '
        address_tree = self.env.company.state_id.name if self.env.company.state_id.name else ' '
        city = self.env.company.city
        if address_one or address_two or address_tree or city:
            return address_one.upper() + ' ' + address_two.upper() + ' ' + city.upper() + ' ' + address_tree.upper()
        else:
            return None


    name = fields.Char(
        string="Référence de l'ordre de virement",
        required=True,
        copy=False,
        readonly=True,
        compute="compute_name"
        )

    

    
    company_address = fields.Char(
        string="Adresse du société",
        default=get_company_address
        )

    virm = fields.Char(default="VIRM")

    order_state = fields.Selection(
        string="État",
        selection=[
            ('new','Nouveau'),
            ('done','Remis'),
            ('cancel','Annuler')
            ],
        default='new'
        )

    beneficiary = fields.Selection(
        string="Bénéficiaires",
        selection=[
            ('employee','Employé'),
            ('supplier','Fournisseur')
            ],
        )


    bank_ids = fields.Many2many(
        'res.bank',
        string="Banques",
        readonly=True
        )

    

    transfer_order_date = fields.Date(
        string="Date de l'ordre de virement",
        default=datetime.today()
        )

    company_id = fields.Many2one(
        'res.company',
        string="Société",
        default=lambda self: self.env.company,
        readonly=True,
        )

    currency_id = fields.Many2one('res.currency',
        string ='Devise',
        related="company_id.currency_id",
        readonly=True,
        )

    order_giver = fields.Many2one(
        'res.partner',
        string="Donneur d'ordre",
        related="company_id.partner_id",
        required=True,
        )


    giver_name = fields.Char(
        string="Nom et Prénom ou raison sociale",
        compute="get_giver_name",
        required=True,
        )


    giver_address = fields.Char(
        string="Adresse du donneur d'ordre",
        compute="get_giver_address",
        required=True
        )


    giver_bank_account_id = fields.Many2one(
        'res.partner.bank',
        string="Compte bancaire",
        domain="[('partner_id', '=', order_giver)]",
        required=True
        )

    giver_rib = fields.Char(
        string="RIB",
        related="giver_bank_account_id.acc_number",
        required=True
        )

    first_tree_rib = fields.Char(
        compute="compute_first_tree_rib"
        )

    operation_number = fields.Integer(
        string="Nombre d'opération de la remise",
        compute="compute_operation_number",
        required=True
        )

    

    global_amount = fields.Monetary(
        string="Montant globale",
        compute="compute_global_amount",
        required=True
        )

    transfer_order_line_ids = fields.One2many(
        'elo.transfer.order.line',
        'transfer_order_id',
        string="Ligne d'ordre de virement"
        )

    note = fields.Text(
        string="Note"
        )



    # -------Computes-----------
    @api.depends('order_giver')
    def get_giver_address(self):
        for record in self:
            giver_address_one = record.order_giver.private_street
            giver_address_two = record.order_giver.private_street2
            c = "°"
            for x in range(len(c)):
                if giver_address_two:
                    giver_address_two = str(giver_address_two).replace(c[x],"")
            if not giver_address_one or not giver_address_two:
                raise models.ValidationError("Veuillez compléter l'adresse de donneur.")
            else:
                record.giver_address = giver_address_one + ' ' + giver_address_two


    @api.depends('transfer_order_date')
    def compute_name(self):
        for record in self:
            month = ' '
            year = ' '
            if record.transfer_order_date:
                month = str(record.transfer_order_date.month)
                year = str(record.transfer_order_date.year)
                record.name = month + year[-2:]
            else:
                record.name = '0'






    @api.depends('order_giver')
    def get_giver_name(self):
        for record in self:
            if not record.company_id.forme_juridique:
                record.giver_name = record.company_id.partner_id.name
            else:
                record.giver_name = record.company_id.forme_juridique.code + ' ' + record.company_id.partner_id.name


    @api.depends('transfer_order_line_ids')
    def compute_global_amount(self):
        '''Montant globale c'est la somme des montants des lignes de la remise'''
        for record in self:
            i = 0
            record.global_amount = 0.0
            for line in record.transfer_order_line_ids:
                i += line.operation_amount
                record.global_amount = i


    @api.depends('transfer_order_line_ids')
    def compute_operation_number(self):
        '''Nombre d'opération c'est le nombre des lignes de la remise'''
        for record in self:
            j = 0
            record.operation_number = 0.0
            for l in record.transfer_order_line_ids:
                j += 1
                record.operation_number = j



    



    @api.depends('giver_rib')
    def compute_first_tree_rib(self):
        for record in self:
            if record.giver_rib:
                numbers = ''.join(filter(str.isdigit, record.giver_rib))
                record.first_tree_rib = numbers[:3]
            else:
                record.first_tree_rib = ''




    

    #Générer l'ordre de virement
    def generate_transfer_order(self):
        if not self.transfer_order_line_ids:
            raise models.ValidationError("Veuillez sélectionner les bénéficiaires SVP...")

        def give_char(char ,taille):
            if len(char) < taille:
                i = taille - len(char)
                char += i * ' '
            return char

        #====================VARIABLES========================#
        file_name = "transfer_order.txt"
        path = "/var/lib/odoo/" + file_name

        val = ""

        filler = ' '


        #Variable pour 'Nature de type d'opération'(Pour le moment ce n'est pas encore identifier)
        operation_type_nature = '010'

        #Nature des fonds
        fonds_nature = "0"

        #Indicateur de présence RIB/BAN
        rib_ban = "1"

        #====================FIN VARIABLES========================#



        
        #VIRM
        val += self.virm

        #Identifiant de la banque du donneur d’ordre(Trois chiffres premiers de RIB)
        val += give_char(str(self.first_tree_rib), 3)


        #Nature de type d'opération sur 3 chiffres
        val += give_char(str(operation_type_nature), 3)


        #Nature des fonds sur 1 chiffre
        val += give_char(str(fonds_nature), 1)


        #Indicateur de présence RIB/BAN sur 1 chiffre
        val += give_char(str(rib_ban), 1)

        char = " "
        for x in range(len(char)):
            if self.giver_rib:
                var_giver_rib = str(self.giver_rib).replace(char[x],"")

        #RIB sur 20 caractère
        val += give_char(str(var_giver_rib), 20)

        #Suite de 4 ÉSPACES
        val += "    "


        #giver_name sur 50 caractère
        val += give_char(str(self.giver_name.upper()), 50)

        #giver_address sur 70 caractère
        val += give_char(str(self.company_address.upper()), 70)


        characters = "'!\?/-"
        for x in range(len(characters)):
            if self.transfer_order_date:
                order_date = str(self.transfer_order_date).replace(characters[x],"")


        #transfer_order_date sur 8 caractère
        val += give_char(order_date, 8)


        
        #Réference de la remise sur 3 chiffres
        val += give_char(self.name, 3)


        #Numéro de l'opération dans la remise sur 6 chiffres
        val += give_char(str(self.operation_number).zfill(6), 6)
        '''Il faut l\'afficher comme ça 000009'''


        #global_amount sur 16 caractère
        val += give_char(str("{:.2f}".format(self.global_amount)).replace(".", "").zfill(16), 16)
         
        '''Pour ne pas afficher la virgule'''


        #Filler
        val += give_char(str(filler), 31) + "\n"



        for line in self.transfer_order_line_ids:



            #name sur 10 caractère
            val += give_char(str(line.name).zfill(6), 6)
            val += give_char(str(self.name).zfill(4), 4)

            #Indicateur de présence RIB/BAN sur 1 chiffre
            val += give_char(str(rib_ban), 1)


            #rib sur 20 caractère
            x_char = " "
            var_line_rib = ''
            for x in range(len(x_char)):
                if line.rib:
                    var_line_rib = str(line.rib).replace(x_char[x],"")
            val += give_char(str(var_line_rib), 20)


            #Suite de 4 ÉSPACES (Préfix IBAN)
            val += "    "


            #partner_name sur 50 caractère
            val += give_char(str(line.partner_name), 50)


            

            #beneficiary_address sur 70 caractère
            val += give_char(str(line.beneficiary_address), 70)

            #operation_amount sur 15 caractère
            line_amount = str("{:.2f}".format(line.operation_amount)).replace(".", "")
            val += give_char(line_amount.zfill(15), 15)
            '''Pour ne pas afficher la virgule'''
            

            #label sur 70 caractère
            if line.label:
                val += give_char(str(line.label.upper()), 70)
            else:
                val += "\n"


            #FILLER
            val += give_char(str(filler), 80) + "\n"


        #Fin
        val += "FVIR"
        #Filler
        val += give_char(str(filler), 96) + "\n"

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
                'res_model': 'elo.transfer.order',
                'datas' : binary_file,
                'type': 'binary',
                })
        else :
            attachment.sudo().write({'datas': binary_file})

        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_transfer_order?filename=%s'%(file_name),
             'target': 'self',
        }


    #Annuler l'ordre de virement
    def cancel_order(self):
        self.order_state = "cancel"


    #Confirmer l'ordre de virement
    def confirm_order(self):
        self.order_state = "done"

        


