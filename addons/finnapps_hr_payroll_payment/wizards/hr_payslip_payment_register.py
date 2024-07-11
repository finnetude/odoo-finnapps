from odoo import models, fields, api, _
from datetime import date,datetime
from odoo.exceptions import UserError, ValidationError



class HrPayslipPaymentRegister(models.TransientModel):

    _name = 'hr.payslip.payment.register'
    _description= "Enregistrer un paiement de bulletin de paie"

    


    payslip_id = fields.Many2one(
        'elo.hr.payslip',
        string="Bulletin de paie"
        )

    currency_id = fields.Many2one(
        'res.currency', 
        string="Devise"
        )

    payslip_run_id = fields.Many2one(
        'elo.hr.payslip.run',
        string="Lot de bulletin de paie"
        )

    payment_type = fields.Selection(
        string="Type de paiement",
        selection=[
            ('payslip','Bulletin de paie'),
            ('payslip_run','Lot de bulletin de paie')])

    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        domain="[('type', 'in', ['cash','bank'])]"
        )

    settlement_date = fields.Date(
        string="Date de règlement",
        default=datetime.today()
        )

    amount = fields.Monetary(
        string="Montant",
        )


    

    # amount_to_pay = fields.Monetary(
    #     string="Montant à payé",
        
    #     )#related="payslip_id.still_to_pay"

    # diff = fields.Float(
    #     string="Différence",
    #     compute="compute_diff"
    #     )

    # for_diff = fields.Boolean(
    #     string="Pour différence",
    #     )

    # for_message = fields.Boolean(
    #     string="Pour message",
    #     )


    memo = fields.Char(
        string="Mémo",
        compute="compute_memo")


    """------------------------Computes------------------------"""
    
    @api.depends('payslip_id')
    def compute_memo(self):
        for record in self:
            if record.payslip_id:
                record.memo = record.payslip_id.number
            elif record.payslip_run_id:
                record.memo = record.payslip_run_id.name


    # @api.depends('amount_to_pay','amount')
    # def compute_diff(self):
    #     for record in self:
    #         record.diff = abs(record.amount_to_pay - record.amount)

    """------------------------End computes------------------------"""

    #-----------------------------------------------------------------#
    

    """------------------------Onchanges------------------------"""

    

    # @api.onchange('payment_type')
    # def onchange_amount_to_pay(self):
    #     if self.payment_type == 'payslip_run':
    #         self.amount_to_pay = 0.0
    

    





    # @api.onchange('amount_to_pay','amount')
    # def onchange_for_diff(self):
    #     if self.amount >= self.amount_to_pay:
    #         self.for_diff = True
    #     else:
    #         self.for_diff = False
    


    # @api.onchange('amount_to_pay','amount')
    # def onchange_for_message(self):
    #     if self.amount > self.amount_to_pay:
    #         self.for_message = True
    #     else:
    #         self.for_message = False



    

    """------------------------End onchanges---------------------------"""
            


    """------------------------Enregistrer un paiement------------------------"""
    def register(self):
        for record in self:
            # move = False
            # if record.amount > record.amount_to_pay:
            #     raise UserError('Vous ne pouvez pas payé un montant supérieur au reste à payé.')
            moves = self.env['account.move']                            #Pièces comptables
            account = ''                                                #Variable pour mettre le compte de ligne NET
            payslip_line = record.payslip_id.line_ids
            for l in payslip_line:
                if l.code == 'NET':
                    account = l.salary_rule_id.account_credit.id        #Récupérer le compte de la ligne NET
            partner = record.payslip_id.employee_id.address_id.id  #Récupérer l'adresse personnelle de l'employé
            if record.payslip_id:
                m_payslip = moves.create({                                          #Créaction d'une pièces comptables
                        'journal_id':record.journal_id.id,
                        'date':record.settlement_date,
                        'ref':record.memo,
                        'line_ids': [
                            (0, 0, {
                                'partner_id': partner,
                                'account_id': account,
                                'name': 'Salaire NET',
                                'debit':record.amount,
                            }),
                            (0, 0, {
                                'partner_id': partner,
                                'account_id': record.journal_id.default_account_id.id,
                                'name': 'Paiement employé {}'.format(record.payslip_id.employee_id.name),
                                'credit':record.amount,
                            }),
                        ],


                    })

                m_payslip.action_post()
                payslip_credit_item = self.env['account.move.line'].search([('name','=','Salaire NET'),('move_id','=',m_payslip.id)], limit=1)

                payslip_debit_item_inv = self.env['account.move.line'].search([('ref','=',record.payslip_id.number),('name','=','Salaire Net')])
                (payslip_credit_item + payslip_debit_item_inv).reconcile()
                record.payslip_id.hr_payment_state = 'paid'
                record.payslip_id.payments_ids = [(6, 0, m_payslip.ids)]
                record.payslip_id.payment_date = date.today()

                


            elif record.payslip_run_id:
                j = 0
                account_run = ''
                for slip in record.payslip_run_id.slip_ids:
                    for line in slip.line_ids:
                        if line.code == 'NET':
                            j+= line.amount
                            account_run = line.salary_rule_id.account_credit.id
                            m_payslip_run = moves.create({                                          #Créaction d'une pièces comptables
                                    'journal_id':record.journal_id.id,
                                    'date':record.settlement_date,
                                    'ref':record.memo,
                                    'line_ids': [
                                        (0, 0, {
                                            'partner_id': partner,
                                            'account_id': account_run,
                                            'name': 'Salaire NET',
                                            'debit':j,
                                        }),
                                        (0, 0, {
                                            'partner_id': partner,
                                            'account_id': record.journal_id.default_account_id.id,
                                            'name': 'Paiement employé {}'.format(record.payslip_run_id.name),
                                            'credit':j,
                                        }),
                                    ],


                                })
                            m_payslip_run.action_post()
                            slip.hr_payment_state = 'paid'
                            slip.payment_date = date.today()



                lot_credit_item = self.env['account.move.line'].search([('name','=','Salaire NET'),('move_id','=',m_payslip_run.id)], limit=1)
                for ln in record.payslip_run_id.slip_ids:
                    payslip_debit_item = self.env['account.move.line'].search([('ref','=',ln.number),('name','=','Salaire Net')])
                    (lot_credit_item + payslip_debit_item).reconcile()
                    ln.payment_date = date.today()
                    ln.payments_ids = [(6, 0, m_payslip_run.ids)]
                record.payslip_run_id.hr_run_payment_state = 'paid'






