from odoo import models, fields, api
import logging as log



class FinnTransferOrderBeneficiary(models.TransientModel):

    _name = 'finn.transfer.order.beneficiary'
    _description= "Bénéficiaires de l'Ordre de virement"


    bank_order_id = fields.Many2one(
        'finn.transfer.order',
        string="Ordre de virement"
        )

    beneficiary_ids = fields.Many2many(
        "res.partner",
        string="Bénéficiaires",
        )

    
    def validate(self):
        if not self.beneficiary_ids:
            raise models.ValidationError("Veuillez ajouter des bénéficiaires")
        for record in self:
            for beneficiary in record.beneficiary_ids:
                transfer_order_line = record.env['finn.transfer.order.line']
                beneficiary_bank_account = record.env['res.partner.bank'].search([('partner_id','=',beneficiary.id)],limit=1)
                values = {
                    'transfer_order_id': record.bank_order_id.id,
                    'beneficiary_id':beneficiary.id,
                    'bank_account_id': beneficiary_bank_account.id,
                    }
                transfer_order_line.create(values)


