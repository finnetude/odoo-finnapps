from odoo import models, fields, api, _

import odoo.addons.decimal_precision as dp

class ResCompany(models.Model):
    _inherit = 'res.company'

    activity_code_id    = fields.Many2many('finn.activity.code', compute='finn_compute_fiscal_information', inverse='finn_inverse_activity_code_id', string ="Code d'activité", index=True)
    forme_juridique_id  = fields.Many2one('finn.forme.juridique', compute='finn_compute_fiscal_information', inverse='finn_inverse_forme_juridique_id', string="Forme juridique")
    nis                 = fields.Char(string="N.I.S",  compute='finn_compute_fiscal_information', inverse='finn_inverse_nis',help="Numéro d'identification statistique")
    nif                 = fields.Char(string="N.I.F", compute='finn_compute_fiscal_information', inverse='finn_inverse_nif', help="Numéro d'identification fiscale")
    fax                 = fields.Char(string="Fax", compute='finn_compute_fiscal_information', inverse='finn_inverse_fax',  size=64)
    capital_social      = fields.Float(string="Capital Social", digits=dp.get_precision('Account'))

    def finn_compute_fiscal_information(self):
        for company in self.filtered(lambda company: company.partner_id):
            company.update({
                'activity_code_id':company.partner_id.activity_code_id,
                'forme_juridique_id':company.partner_id.forme_juridique_id,
                'nis':company.partner_id.nis,
                'nif':company.partner_id.nif,
                'fax':company.partner_id.fax,
            })

    def finn_inverse_activity_code_id(self):
        for company in self:
            company.partner_id.activity_code_id = company.activity_code_id

    def finn_inverse_forme_juridique_id(self):
        for company in self:
            company.partner_id.forme_juridique_id = company.forme_juridique_id

    def finn_inverse_nis(self):
        for company in self:
            company.partner_id.nis = company.nis

    def finn_inverse_nif(self):
        for company in self:
            company.partner_id.nif = company.nif

    def finn_inverse_fax(self):
        for company in self:
            company.partner_id.fax = company.fax

# ============================= CHAMPS DE CONFIGURATION ========================================

    # La configuration qui permet de déclarer les factures au paiement ou la comptabilisation 
    based_on                    = fields.Selection([('posted_invoices', 'Factures validées'),
                                                    ('payment', 'Paiements des factures')],
                                                    default="posted_invoices", string="Basé sur")

    # Les configurations qui permetent d'afficher le code/secteur d'activité sur les rapports (Devis)
    industry_id_in_quotation    = fields.Boolean(string ="Secteur d'activité")
    activity_code_in_quotation  = fields.Boolean(string ="Code d'activité")

    # Les configurations qui permettent d'afficher le code/secteur d'activité sur les rapports (Facture)
    industry_id_in_invoice      = fields.Boolean(string ="Secteur d'activité")
    activity_code_in_invoice    = fields.Boolean(string ="Code d'activité")

    # Les configurations qui permettent de choisir le compte et le journal des tax temporaires
    # transfer_tax_journal        = fields.Many2one("account.journal" , string ="Journal de transfert de taxe", default=lambda self: self.env['account.journal'].search([('type', '=','general')], limit=1))
    # temporary_tax_account       = fields.Many2one("account.account" , string ="Compte temporaire de taxe")

# ==============================================================================================


    @api.onchange('name','capital_social','phone','fax','email','website','company_registry','vat','nif','nis')
    def onchange_report_footer(self):
        report_footer = f"{self.name} au capital social: {self.capital_social}"

        if self.phone:
            report_footer += f", Tél: {self.phone}"
        else:
            report_footer += ","

        if self.fax:
            report_footer += f" | Fax: {self.fax}"

        if self.email:
            report_footer += f" | Courriel: {self.email}\n"
        else:
            report_footer += "\n"

        if self.website:
            report_footer += f" | Site web: {self.website}"

        if self.company_registry:
            report_footer += f" | RC N°: {self.company_registry}"

        if self.vat:
            report_footer += f" | AI: {self.vat}"

        if self.nif:
            report_footer += f" | NIF: {self.nif}"

        if self.nis:
            report_footer += f" | NIS: {self.nis}"

        self.report_footer = report_footer

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    based_on                    = fields.Selection([('posted_invoices', 'Factures validées'),
                                                    ('payment', 'Paiements des factures')],
                                                    default="posted_invoices", string="Basé sur")

    industry_id_in_quotation    = fields.Boolean(string ="Secteur d'activité")
    activity_code_in_quotation  = fields.Boolean(string ="Code d'activité")

    industry_id_in_invoice      = fields.Boolean(string ="Secteur d'activité")
    activity_code_in_invoice    = fields.Boolean(string ="Code d'activité")

    # transfer_tax_journal        = fields.Many2one("account.journal" , string ="Journal de transfert de taxe", default=lambda self: self.env['account.journal'].search([('type', '=','general')], limit=1))
    # temporary_tax_account       = fields.Many2one("account.account" , string ="Compte temporaire de taxe" )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        company and res.update(
            based_on                    = company.based_on,
            industry_id_in_quotation    = company.industry_id_in_quotation,
            activity_code_in_quotation  = company.activity_code_in_quotation,
            industry_id_in_invoice      = company.industry_id_in_invoice,
            activity_code_in_invoice    = company.activity_code_in_invoice,
            # transfer_tax_journal        = company.transfer_tax_journal,
            # temporary_tax_account       = company.temporary_tax_account,
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        company = self.env.company
        company and company.write({          
            'based_on'                  : self.based_on,
            'industry_id_in_quotation'  : self.industry_id_in_quotation,
            'activity_code_in_quotation': self.activity_code_in_quotation,
            'industry_id_in_invoice'    : self.industry_id_in_invoice,
            'activity_code_in_invoice'  : self.activity_code_in_invoice,
            # 'transfer_tax_journal'      : self.transfer_tax_journal,
            # 'temporary_tax_account'     : self.temporary_tax_account,
        })
        return res