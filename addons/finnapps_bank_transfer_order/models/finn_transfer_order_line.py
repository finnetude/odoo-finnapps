from odoo import models, fields, api,_
from datetime import date

class FinnTransferOrderLine(models.Model):
    
    _name = "finn.transfer.order.line"
    _description = "Ligne d'ordre de virement"


    name = fields.Char(
        string="Numéro d'ordre l'opération",
        compute="get_operation_number",
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

    beneficiary_id = fields.Many2one(
        "res.partner",
        string="Bénéficiaire",
        required=True,
        )

    partner_name = fields.Char(
        string="Nom et Prénom ou raison sociale",
        related="beneficiary_id.name",
        required=True,
        )

    beneficiary_address = fields.Char(
        string="Adresse du bénéficiaire",
        compute="get_beneficiary_address",
        required=True
        )


    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string="Compte bancaire",
        domain="[('partner_id', '=', beneficiary_id)]",
        )


    rib = fields.Char(
        string="RIB",
        related="bank_account_id.acc_number",
        required=True
        )

    operation_amount = fields.Monetary(
        string="Montant de l'opération",
        digits=(14, 2)
        )


    label = fields.Char(
        string="Libellé",
        )


    transfer_order_id = fields.Many2one(
        'finn.transfer.order',
        )


    @api.depends('beneficiary_id')
    def get_beneficiary_address(self):
        for record in self:
            address_one = record.beneficiary_id.street
            address_two = record.beneficiary_id.street2
            address_tree = record.beneficiary_id.state_id.name
            city = record.beneficiary_id.city
            if not address_one:
                raise models.ValidationError("Veuillez compléter l'adresse de bénéficiaire.")
            else:
                record.beneficiary_address = address_one + ' ' + city + ' ' + address_tree


    #Pour les numéros de lignes
    def get_operation_number(self):
        i = 0
        for record in self:
            i += 1
            record.name = i




