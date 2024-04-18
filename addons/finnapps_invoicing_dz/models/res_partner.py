from odoo import models, fields, api, _

from collections import defaultdict
import logging as log

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    activity_code_id    = fields.Many2many('finn.activity.code' , string ="Code d'activité", index=True)
    forme_juridique_id  = fields.Many2one('finn.forme.juridique', string="Forme juridique")
    forme_juridique_code = fields.Char(string="Code de la forme juridique", related="forme_juridique_id.code")
    nis                 = fields.Char(string="N.I.S", help="Numéro d'identification statistique")
    nif                 = fields.Char(string="N.I.F", help="Numéro d'identification fiscale")
    fax                 = fields.Char(string="Fax", size=64)

    def _prepare_display_address(self, without_company=False):
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = defaultdict(str, {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
            'forme_juridique_code': self.forme_juridique_code or '',
        })

        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s, %(forme_juridique_code)s,\n' + address_format
        return address_format, args

    
