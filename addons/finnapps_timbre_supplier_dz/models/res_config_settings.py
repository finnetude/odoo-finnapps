from odoo import models, fields, api, _

        
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
 
    purchase_offset_account = fields.Many2one('account.account', string ="Compte contrepartie achat", )
 
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company

        company and res.update(
            
            purchase_offset_account= company.purchase_offset_account.id,
        
        )
        return res


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        company = self.env.company
        company and company.write({
          
            'purchase_offset_account': self.purchase_offset_account.id,
        
        })
        return res