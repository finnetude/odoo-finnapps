from datetime import date
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import logging as log


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    add_droit_timbre = fields.Boolean(string="Ajouter un droit de timbre fournisseur")
    droit_timbre_supplier = fields.Monetary(string="Droit de timbre fournisseur")
    supplier_move_id = fields.Many2one('account.move', string="Pièce comptable fournisseur")
    supplier_move_name = fields.Char(string="Nom de pièce comptable de timbre fournisseur", related='supplier_move_id.name')


    """Un champ boolean utilisé pour la visibilté d'autre champs en fonction de la valeur de champ  'Se basé sur' """
    for_based_on = fields.Boolean(string="Pour le champ 'Se basé sur'", compute="_compute_for_based_on")

    """Un champ boolean utilisé pour la visibilté d'autre champs en fonction de la valeur de champ  'Journal' """
    for_journal_id = fields.Boolean(string="Pour le champ 'Journal'", compute="_compute_for_journal_id")


    '''Un champ qui montre si la pièce comptable a été crée'''
    create_move_id = fields.Boolean(string="Créer une pièce comptable", default=True)

    @api.onchange('partner_type')
    def onchange_for_partner_type(self):
        if self.partner_type != 'supplier': 
            self.droit_timbre_supplier = 0
            self.add_droit_timbre = False
    

    @api.depends('journal_id')
    def _compute_for_journal_id(self):
        if self.journal_id.type == "cash":
            self.for_journal_id = True

        else:
            self.for_journal_id = False
            self.droit_timbre_supplier = 0
            self.add_droit_timbre = False


    @api.onchange('journal_id')
    def _onchange_timbre(self):
        if self.journal_id.type != "cash":
            self.droit_timbre_supplier = 0
            self.add_droit_timbre = False

    @api.depends('journal_id','partner_id')
    def _compute_for_based_on(self):
        if self.company_id.based_on == "posted_invoices":
            self.for_based_on = False
        else:
            self.for_based_on = True


    @api.onchange('add_droit_timbre')
    def onchange_droit_timbre(self):
        if self.add_droit_timbre == False:
            self.droit_timbre_supplier = 0.0
        if self.droit_timbre_supplier < 0.0:
            raise models.ValidationError("Le montant de droit de timbre doit être positif")





    '''Création des lignes de la pièce comptable'''
    def create_move_timbre_supplier(self):
        for record in self:
            
            if record.add_droit_timbre:
                
                journal = self.env['account.journal'].search([('for_supplier_timbre','=', True)],limit=1)
                if not journal:
                    
                    raise ValidationError('Il n\'existe pas un journal Pour timbre fournisseur.')
                default_account = self.env['account.account'].search([
                                                    ('internal_group', '=', 'liability'),
                                                    ], limit=1).id
                record.supplier_move_id = self.env['account.move'].create({
                    'move_type': 'entry',
                    'journal_id': journal.id,
                    'line_ids': [
                        (0, 0, {
                            'name': 'Droit de timbre fournisseur',
                            'partner_id':record.partner_id.id if record.partner_id else False,
                            'account_id':record.partner_id.property_account_payable_id.id if record.partner_id.property_account_payable_id.id else default_account,
                            'debit':record.droit_timbre_supplier,
                        }),
                        (0, 0, {
                            'name': 'Droit de timbre fournisseur',
                            'partner_id':record.partner_id.id if record.partner_id else False,
                            'account_id': record.company_id.purchase_offset_account.id,
                            'credit':record.droit_timbre_supplier,
                        }),
                    ],
                    
                })

    '''Création des lignes de la pièce comptable'''
    def write_move_timbre_supplier(self, vals):
        for record in self:
            #date = date.today()
            if record.add_droit_timbre and record.droit_timbre_supplier > 0:
                if record.name != record.supplier_move_id.name :
                    record.supplier_move_id.write({'ref': record.name})
                record.supplier_move_id.line_ids.unlink()
                default_account = self.env['account.account'].search([
                                                    ('internal_group', '=', 'liability'),
                                                    ], limit=1).id
                record.supplier_move_id.write({

                    'line_ids': [
                        (0, 0, {
                            'name': 'Droit de timbre fournisseur',
                            'partner_id':record.partner_id.id if record.partner_id else False,
                            'account_id': record.partner_id.property_account_payable_id.id if record.partner_id.property_account_payable_id.id else default_account,
                            'debit':record.droit_timbre_supplier,
                        }),
                        (0, 0, {
                            'name': 'Droit de timbre fournisseur',
                            'partner_id':record.partner_id.id if record.partner_id else False,
                            'account_id': record.company_id.purchase_offset_account.id,
                            'credit':record.droit_timbre_supplier,
                        }),
                    ],
                    
                })

    def button_open_invoice_supplier(self):
        ''' Redirect the user to the invoice(s) paid by this payment.
        :return:    An action on account.move.
        '''
        self.ensure_one()

        action = {
            'name': _("Paid Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.supplier_move_id.id,
        }
        
        
        return action

    @api.model
    def create(self, vals):
        journal = self.env['account.journal'].search([('id','=', vals['journal_id'])])
        if journal.type == 'cash' and 'add_droit_timbre' in vals:
            if vals['add_droit_timbre'] == True:
                vals['create_move_id'] = True
        res = super(AccountPayment, self).create(vals)
        '''Générer les lignes de la pièce compatable'''
        res.create_move_timbre_supplier()
        if res.state == 'posted':
            res.supplier_move_id.action_post()
        return res


    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        if self.supplier_move_id:
            if self.journal_id.type != 'cash' or self.add_droit_timbre == False:
                if self.supplier_move_id.state == 'posted':
                    '''Mettre la pièce comptable en broullion'''
                    self.supplier_move_id.button_draft()
                '''Annuler la pièce comptable'''
                self.supplier_move_id.button_cancel()
                return res

            if self.supplier_move_id.state in ['cancel','posted']:
                '''Mettre la pièce comptable en broullion'''
                self.supplier_move_id.button_draft()
            '''Regénérer les lignes de la pièce comptable'''
            self.write_move_timbre_supplier(vals)
            
        else :
            if not self.create_move_id == False and 'add_droit_timbre' in vals:
                if vals['add_droit_timbre'] == True:
                    self.create_move_timbre_supplier()
        if self.state == 'posted':
            self.supplier_move_id.action_post()
        return res

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        if self.supplier_move_id.state == 'draft':
            self.supplier_move_id.action_post()
        return res

    def action_cancel(self): 
        res = super(AccountPayment, self).action_cancel()
        self.supplier_move_id.button_cancel()
        return res

    def action_draft(self):         
        self.supplier_move_id.button_draft()

        res = super(AccountPayment, self).action_draft()
        return res


    def unlink(self):
        for record in self:
            if self.supplier_move_id:
                self.with_context(force_delete=True).supplier_move_id.unlink()
        return super(AccountPayment, self).unlink()



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'


    use_timbre_supplier = fields.Boolean(compute='_visible_timbre_fiscal')

    amount_timbre_supplier = fields.Monetary(string = "Droit de timbre fournisseur", digits = (2))


    def _create_payment_vals_from_wizard(self, batch_result):

        result = super()._create_payment_vals_from_wizard(batch_result)

        result['droit_timbre_supplier'] = self.amount_timbre_supplier
       
        if self.amount_timbre_supplier:

            result['add_droit_timbre']  = True

        return result


    @api.onchange('journal_id')
    def _onchange_amount_timbre_supplier(self):
        if not self.use_timbre_supplier:
            self.amount_timbre_supplier = 0

    @api.depends('journal_id')
    def _visible_timbre_fiscal(self):
        for payment in self:
            payment.use_timbre_supplier = True if payment.journal_id.type == 'cash' and payment.partner_type == "supplier" and payment.company_id.based_on == 'payment' else False
            

    
  


   
