from odoo import models, fields, api, _
import datetime

class FinnLiasseFiscale(models.Model):
    _name = "finn.liasse.fiscale"
    _description = "Liasse fiscale"

# ====================================== DEFAULT ========================================
    def _default_exercice(self):
        exercice_id = self.env['finn.exercice'].search([('name','=',str(datetime.datetime.now().year))], limit=1)
        if exercice_id:
            return exercice_id.id
        return False

# ====================================== DOMAIN ========================================
# ====================================== CHAMPS ========================================

    name = fields.Char('Nom', readonly=True, required=True, copy=False, compute='_compute_name')

    company_id = fields.Many2one('res.company', string='Société', readonly=True, default=lambda self: self.env.company.id)

    state = fields.Selection(string='State', selection=[('draft', 'Brouillon'), ('lock', 'Verouillé')], default='draft',)
    
    notes = fields.Text('Notes')

    switch_button = fields.Boolean(default=False)

    type_liasse = fields.Selection(string='Type de document', selection=[('comptable', 'Comptable'), ('fiscale', 'Fiscale')], required=True, default='comptable')

    lock_date = fields.Datetime('Date de verrouillage', readonly=True)

    exercice_id = fields.Many2one('finn.exercice', string = 'Exercice', required=True, default=_default_exercice)

    report_liasse_fiscal_ids = fields.One2many('finn.liasse.fiscale.report','liasse_fiscal_id', string ='Rapprot de liasse fiscal')

# ====================================== ONCHANGES ========================================

# ====================================== COMPUTES ========================================
    @api.depends('exercice_id','type_liasse')
    def _compute_name(self):
        for record in self:
            if record.exercice_id:
                record.name = "Liasse fiscale de {} ({})".format(record.exercice_id.name, record.type_liasse)
            else:
                record.name = "Nouveau"

# ====================================== OVERRIDE ========================================

    @api.model
    def create(self, vals):
        result = super(FinnLiasseFiscale,self).create(vals)
        if result.type_liasse == 'comptable':
            reports_type = [
                'bilan_actif','bilan_passif','compte_resultat',
                'tableau_flux_tresorerie']
            
        elif result.type_liasse == 'fiscale':
            reports_type = [
                'bilan_actif','bilan_passif','compte_resultat',
                'stock','charge','amo_inv','cess_prov',
                'perte_val','result','tab','commission']
            
        create_report = []
        for report in reports_type:
            create_report.append((0,0,{
                'liasse_fiscal_id': result.id,
                'type_report': report,
                }))
            
        result.update({
            'report_liasse_fiscal_ids':create_report
        })
        return result
    
    def unlink(self):
        for report in self.report_liasse_fiscal_ids:
            report.unlink()
        super(FinnLiasseFiscale,self).unlink()


# ====================================== BOUTONS ========================================

    def to_draft(self):
        self.state = "draft"
        self.lock_date = False

    def to_lock(self):
        for report in self.report_liasse_fiscal_ids:
            report.to_lock()
        self.state = "lock"
        self.lock_date = datetime.datetime.now()
        self.switch_button = False

    def reinitialisation(self):
        for report in self.report_liasse_fiscal_ids:
            report.reinitialisation()

    def calculate_line(self):
        for report in self.report_liasse_fiscal_ids:
            report.calculate_line()
        self.write({'switch_button': True})
        
    def recalculate_line(self):
        for report in self.report_liasse_fiscal_ids:
            report.recalculate_line()

# ====================================== ACTION PRINT ======================================== 

    def action_report_full(self):
        return self.env.ref('finnapps_liasse_fiscale_dz.action_muli_report').report_action(self)
