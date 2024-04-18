from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp

# ====================================== CONSTANTES ========================================

class ReportG50Line(models.Model):
    _name = 'report.g50.line'
    _description = 'Lignes de rapport G50'

    name = fields.Char(string="Nom")
    
    code = fields.Char('Code')

    definition = fields.Char(string='Opérations imposables')

    ratio = fields.Many2one('config.g50.ratio', string="Taux")

    type_line = fields.Selection([('tap', 'TAP'),('ibs', 'IBS'),('irg', 'IRG'),('timbre', 'Droits de timbre'),('autre', 'Autre Impôt et Taxes'),('tva_9', 'TVA 9%'),('tva_19', 'TVA 19%'),('deduction', 'Déduction à opérer'),('tva_p', 'TVA à payer'),], required=True)
    
    amount = fields.Float(digits=dp.get_precision('Account'), string="Montant")

    amount_exo = fields.Float(digits=dp.get_precision('Account'))

    imposable = fields.Float(digits=dp.get_precision('Account'))

    total = fields.Float(digits=dp.get_precision('Account'))

# ====================================== LIAISON AVEC LE RAPPORT ========================================
    
    # Tableau TAP
    report_tap_id = fields.Many2one('report.g50')
    
    # Tableau IBS
    report_ibs_id = fields.Many2one('report.g50')

    # Tableau IRG
    report_irg_id = fields.Many2one('report.g50')
    
    # Tableau Droits de timbre
    report_timbre_id = fields.Many2one('report.g50')
    
    # Tableau Autre Impôt et Taxes
    report_autre_id = fields.Many2one('report.g50')
    
    # Tableau TVA 9%
    report_tva_9_id = fields.Many2one('report.g50')
    
    # Tableau TVA 19%
    report_tva_19_id = fields.Many2one('report.g50')
    
    # Tableau Déduction à opérer
    report_deduction_id = fields.Many2one('report.g50')
    
    # Tableau TVA à payer
    report_tva_p_id = fields.Many2one('report.g50')

# ====================================== ONCHANGE ========================================

    @api.onchange('ratio', 'amount')
    def onchange_ratio(self):
        if self.ratio and self.ratio.ratio:
            self.total = self.amount * self.ratio.ratio / 100

    @api.onchange('amount', 'amount_exo')
    def onchange_imposable(self):
        if self.type_line in ['tva_9','tva_19']:
            self.imposable = self.amount - self.amount_exo