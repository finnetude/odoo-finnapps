from odoo import models, fields, api

class FinnLiasseFiscaleType(models.Model):
    _name = "finn.liasse.fiscale.type"
    _description = "Type rapport de la liasse fiscale"

    name = fields.Char('Nom', required=True, copy=False)
    code = fields.Char('Code', required=True, copy=False)
    type_liasse = fields.Selection(string='Type de document', selection=[('comptable', 'Comptable'), ('fiscale', 'Fiscale')], required=True, default='comptable',)
    line_ids = fields.One2many('finn.liasse.fiscale.type.line','report_id', string="Configuration de liasse fiscale")
    notes = fields.Text('Notes')

    _sql_constraints = [
        ('unique_code', 'UNIQUE (code)', "Le code doit être unique"),
    ]

class FinnLiasseFiscaleTypeLine(models.Model):
    _name = "finn.liasse.fiscale.type.line"
    _description = "Ligne de type de rapport de la liasse fiscale"

    name = fields.Char('Nom')
    code = fields.Char('Code')
    definition = fields.Char('Définition')
    report_id = fields.Many2one('finn.liasse.fiscale.type', string = 'Rapport', required=True)
    config_ids = fields.One2many('finn.liasse.fiscale.config', 'type_line_id', string = 'Configuration')
    display_type = fields.Selection(string='Type de configuration', selection=[('calcule', 'Calcule'), ('total', 'Totale'),('title','Titre')], required=True, default='calcule')

    def action_create_config(self):
        return  {
            'name': "Ajouter un configuration",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'finn.liasse.fiscale.config',
            'context':{'default_type_line_id':self.id},
            'target':'new',
        }

class FinnLiasseFiscaleConfig(models.Model):
    _name = "finn.liasse.fiscale.config"
    _description = "Configuration de rapport de la liasse fiscale"

    name = fields.Char('Nom', required=True, copy=False, compute="_compute_name")

    @api.depends('group_account','operation','inc_exc','colonne_num')
    def _compute_name(self):
        for record in self:
            record.name = '{}:{}:{}'.format(record.colonne_num, record.group_account, record.operation)
    
    @api.depends('inc_exc')
    def _compute_color(self):
        for record in self:
            if record.inc_exc == 'INC':
                record.color = 4
            if record.inc_exc == 'EXC':
                record.color = 1

    # type_config = fields.Selection(string='Type de configuratop,', selection=[('', ''), ('', '')], required=True, default='',)

    type_line_id = fields.Many2one('finn.liasse.fiscale.type.line', string = 'Ligne de type de rapport')

    group_account = fields.Integer(string = 'Groupe de Comptes comptables', required=True)

    operation = fields.Selection(string='Opération sur le', selection=[('D', 'Débit'), ('C', 'Crédit'),('S','Solde')], required=True, default='S',)

    inc_exc = fields.Selection(string='Type', selection=[('INC', 'Inclure'), ('EXC', 'Exclure')], required=True, default='inc',)

    colonne_num = fields.Selection(string='Colonne',
                                    selection= [('ONE','Colonne 1'),
                                                ('TWO','Colonne 2'),
                                                ('THREE','Colonne 3'),
                                                ('FOUR','Colonne 4'),
                                                ('FIVE','Colonne 5'),
                                                ('SIX','Colonne 6')], required=True, default='ONE',)

    color = fields.Integer(compute="_compute_color", store=True)

    def confirm_close_config(self):
        return {'type': 'ir.actions.act_window_close'}
