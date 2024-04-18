from odoo import models, fields, api
from datetime import datetime, date

class HrContract(models.Model):

    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    def _default_structure(self):
        struct = self.env['finn.hr.payroll.structure'].search([('default_structure','=',True)])
        if struct:
            return struct 
        else:
            self.env['finn.hr.payroll.structure']

    struct_id = fields.Many2one('finn.hr.payroll.structure', string='Structure salariale',default=_default_structure)

    analytic_account_id = fields.Many2one('account.analytic.account', 'Compte analytiquet')
    journal_id = fields.Many2one('account.journal', 'Journal salarial', domain="[('type', '=', 'general'),('is_journal_for_pay','=',True)]")

    schedule_pay = fields.Selection([
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semi-annually', 'Semestriel'),
        ('annually', 'Annuellement'),
    ], string='Fréquence de paiement', index=True, default='monthly',
    help="Defines the frequency of the wage payment.")

    resource_calendar_id = fields.Many2one(required=True, string="Heures de travail", help="L'horaire de travail de l'employé.")

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))
    
class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_journal_for_pay = fields.Boolean('Est un journal pour les salaires')
