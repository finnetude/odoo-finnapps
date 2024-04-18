from odoo import models, api

class ResCountry(models.Model):
    _inherit = 'res.country'

    @api.model
    def change_address_format_dz(self):
        self.env.ref('base.dz').write({
            'address_format':"%(street)s\n%(street2)s\n%(zip)s %(city)s (%(state_name)s) %(country_name)s",
            'vat_label':'A.I',
            })