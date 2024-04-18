from odoo import models, fields, _
from odoo.exceptions import  ValidationError

class ConfigG50(models.Model):
    _name = 'config.g50'
    _description = 'Configuration G50'

# ====================================== CHAMPS ========================================

    name = fields.Char(string='Nom', required='True', copy=False, default='Nouvelle configuration')

    type = fields.Selection(string='Type', selection=[('g50', 'Série G n° 50'), ('g50a', 'Série G n° 50 A'), ('g50ter', 'Série G n° 50 ter')], required='True', default='g50')

    readonly_config = fields.Boolean('Non modifiable', copy=False)

    use_invoice_draft = fields.Boolean('Prendre en compte les facutres brouillons')

# ====================================== CHAMPS DES LIGNES ========================================

    line_tap_ids = fields.One2many('config.g50.line', 'report_id', string='Lines',domain=[('type_line', '=', 'tap')], copy=True)

    line_ibs_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'ibs')], copy=True)

    line_irg_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'irg')], copy=True)

    line_timbre_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'timbre')], copy=True)

    line_autre_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'autre')], copy=True)

    line_tva_9_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'tva_9')], copy=True)

    line_tva_19_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'tva_19')], copy=True)

    line_deduction_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'deduction')], copy=True)

    line_tva_p_ids = fields.One2many('config.g50.line', 'report_id', string='Lines', domain=[('type_line', '=', 'tva_p')], copy=True)

    def unlink(self):
        if self.id in [self.env.ref("finnapps_report_g50.config_g50").id, 
                       self.env.ref("finnapps_report_g50.config_g50_a").id,
                       self.env.ref("finnapps_report_g50.config_g50_ter").id]:
            raise ValidationError(_("Vous ne pouvez pas supprimer une configuration standard!"))
        super(ConfigG50,self).unlink()

class g50_line(models.Model):
    _name = 'config.g50.line'
    _description = 'Lignes de configuration G50'

    name = fields.Char('Nom')

    code = fields.Char('Code')

    definition = fields.Char(string='Comptes')

    definition_exo = fields.Char(string='Comptes exonéré')
    
    ratio = fields.Many2one('config.g50.ratio', string="Taux")
    
    type_line = fields.Selection([('tap', 'TAP'),('ibs', 'IBS'),('irg', 'IRG'),('timbre', 'Droits de timbre'),('autre', 'Autre Impôt et Taxes'),('tva_9', 'TVA 9%'),('tva_19', 'TVA 19%'),('deduction', 'Déduction à opérer'),('tva_p', 'TVA à payer')], required=True)
    
    report_id = fields.Many2one('config.g50', 'Configuration G50',)

    line_tva = fields.Boolean('Lignes de configuration TVA G50', default=False)

    use_line = fields.Boolean('Activer la ligne', default=False)

class g50Ratio(models.Model):
    _name = 'config.g50.ratio'
    _description = 'Ratio G50'

    name = fields.Char(string='Code')
        
    type_ratio = fields.Selection([('per', 'Pourcentage'), ('amount', 'Montant')])
    
    ratio = fields.Float(digits=(16, 2))