from odoo import fields, models, api, _

class AccountMoveG50(models.Model):
    _name = 'account.move.g50'
    _description = 'Pièces comptable liées au G50'

    name = fields.Char(compute='_compute_name', store=True)

    report_id = fields.Many2one('report.g50',string='Rapport G50')

    move_id = fields.Many2one('account.move',string='Pièce comptable')

    move_line_ids = fields.Many2many('account.move.line', 'move_move_line_rel', 'move_cln', 'move_line_cln', string='Écriture comptable')

    invoice_line_ids = fields.Many2many('account.move.line', 'invoice_move_line_ref', 'invoice_cln', 'invoice_line_cln', string='Lignes de facturation')

    date = fields.Date(string="Date", related="move_id.date")

    paid_date = fields.Date('Date de paiement', related="move_id.paid_date")

    move_type = fields.Selection(string="Type de pièce", related="move_id.move_type", store=True, readonly=True)

# ====================================== COMPUTE ========================================

    @api.depends('move_id')
    def _compute_name(self):
        for record in self:
            if record.move_id:
                record.name = record.move_id.name
            else:
                record.name = "Nouveau"

# ====================================== ONCHANGE ========================================

    @api.onchange('move_id')
    def onchange_move_line(self):
        for record in self:
            if record.move_id:
                record.move_line_ids = record.move_id.line_ids
            else:
                record.move_line_ids = False
                date = False

    @api.onchange('move_id')
    def onchange_invoice_line(self):
        for record in self:
            if record.move_id:
                record.invoice_line_ids = record.move_id.invoice_line_ids
            else:
                record.invoice_line_ids = False
                date = False