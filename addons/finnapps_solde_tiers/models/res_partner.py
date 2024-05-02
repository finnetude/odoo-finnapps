# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    move_line_ids = fields.One2many(
        string='Ecritures comptable',
        comodel_name='account.move.line',
        inverse_name='partner_id',
    )


    solde = fields.Float(
        string="Solde",
        compute='get_the_solde',
        store=True,
    )

    def get_solde(self):
        sudo = self.sudo()
        sql_receivable = "SELECT id FROM account_account WHERE account_type in ('asset_receivable','liability_payable')"
        sql_posted = "SELECT id FROM account_move WHERE state = 'posted'"
        final_sql = sql_receivable 
        for record in self:
            ids = tuple(record.env['account.move.line'].search([('partner_id','=',record.id),('move_id.state','=', 'posted')]).ids)
            if ids :
                if len(ids) == 1:
                    sql = "select SUM(debit - credit) as solde FROM account_move_line WHERE account_move_line.id IN ({}) and account_id IN ({}) ".format(ids[0], final_sql)
                else:
                    sql = "select SUM(debit - credit) as solde FROM account_move_line WHERE account_move_line.id IN {} and account_id IN({}) ".format(ids, final_sql)


                self.env.cr.execute(sql)
                aml = self.env.cr.dictfetchall()
                # _logger.info("zakkkk 2")
                # _logger.info()
                # _logger.info(aml[0])
                return aml[0]['solde']
        
        return 0
    
    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(ResPartner, self).get_view(view_id,view_type,**options)
    #     all_ids = self.env['res.partner'].search([('active',"=",True)])
    #     for id_item in all_ids:
    #         id_item.get_the_solde()
    #     return res
    
    @api.depends('move_line_ids')
    def get_the_solde(self):
        value = self.get_solde()
        self.solde = value

