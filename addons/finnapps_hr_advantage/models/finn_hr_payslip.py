from odoo import api, models
import logging as log

class FinnHrPayslip(models.Model):
    _inherit = 'finn.hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(FinnHrPayslip, self).get_inputs(contracts, date_from, date_to)

        for contract in contracts:
            # Prendre en compte que les avantages à l'état confirmé
            clause_1 = [('state','=','open'), '|', '|']
            # Un avantage est valable s'il se termine entre les dates indiquées
            clause_2 =['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
            # Ou s'il commence entre les dates données
            clause_3 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
            # Ou s'il commence avant le date_from et se termine après le date_end (ou ne finit jamais)
            clause_4 = ['&', ('date_start', '<=', date_from), ('date_end', '>=', date_to)]
            
            clause_final = clause_1 + clause_2 + clause_3 + clause_4

            advantages = self.env['finn.hr.bonuse.advantage'].search(clause_final)
            if advantages:
                advantages_eligible =[]
                for advantage in advantages:
                    # Si le contrat est lié à l'avantage et si l'avantage est de type contrat
                    # Si aucun contrat n'est lié à l'avantage et si l'avantage est de type contrat
                    # Si l'employé est lié à l'avantage et si l'avantage est de type employé
                    # Si aucun employé n'est lié à l'avantage et si l'avantage est de type employé
                    if  (contract.id in advantage.contract_ids.ids and advantage.type_advantage == 'contract') \
                        or (contract.employee_id.id in advantage.employee_ids.ids and  advantage.type_advantage == 'employe'):
                        # Si la règle de l'avantage fait partie de la stucture
                        if advantage.rule_id.id in contract.struct_id.rule_ids.ids:
                            advantages_eligible += [advantage]

                for advantage_eligible in advantages_eligible:
                    input_data = {
                        'name': advantage_eligible.rule_id.name,
                        'code': advantage_eligible.rule_id.code,
                        'contract_id': contract.id,
                        'amount': advantage_eligible.amount_adv,
                    }
                    res += [input_data]
        return res