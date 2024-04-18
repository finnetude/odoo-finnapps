from odoo import models, fields, api, _

class FinnLiasseFiscale(models.Model):
    _name = "finn.liasse.fiscale.line"
    _description = "Ligne de rapport de la liasse fiscale"

    name = fields.Char('Nom')

    code = fields.Char('Code')

    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company.id)

    display_type = fields.Selection(string='Type de configuration', selection=[('calcule', 'Calcule'), ('total', 'Totale'),('title','Titre')], required=True, default='total')

    date_line = fields.Date(string="Date")

    designation_col_one = fields.Char(string="Désignation  1")
    designation_col_two = fields.Char(string="Désignation  2")

    amount_col_one = fields.Float(string="Colonne 1")
    amount_col_two = fields.Float(string="Colonne 2")
    amount_col_three = fields.Float(string="Colonne 3")
    amount_col_four = fields.Float(string="Colonne 4")
    amount_col_five = fields.Float(string="Colonne 5")
    amount_col_six = fields.Float(string="Colonne 6")

    # Bilan (actif)
    inv_bilan_actif_id = fields.Many2one('finn.liasse.fiscale.report')

    # Bilan (passif)
    inv_bilan_passif_id = fields.Many2one('finn.liasse.fiscale.report')

    # Compte de résultat
    inv_compte_resultat_id = fields.Many2one('finn.liasse.fiscale.report')

    # Tableau des flux de trésorerie
    inv_tableau_flux_tresorerie_id = fields.Many2one('finn.liasse.fiscale.report')

    # 1/ Tableau des mouvements des stocks
    inv_stock_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 2/ Tableau de la fluctuation de la production stockée
    inv_stock_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 3/ Charges de personnel, impôts, taxes et versements assimilés, autres services
    inv_charge_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 4/ Autres charges et produits opérationnels
    inv_charge_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 5/ Tableau des amortissements et pertes de valeurs
    inv_amo_inv_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 6/ Tableau des immobilisations créées ou acquises au cours de l’exercice
    inv_amo_inv_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 7/ Tableau des immobilisations cédées (plus ou moins value) au cours de l’exercice
    inv_cess_prov_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 8/ Tableau des provisions et pertes de valeurs
    inv_cess_prov_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 8/1 Relevé des pertes de valeurs sur créances
    inv_perte_val_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 8/2 Relevé des pertes de valeurs sur actions et parts sociales
    inv_perte_val_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 9/ Tableau de détermination du résultat fiscal
    inv_result_id = fields.Many2one('finn.liasse.fiscale.report')

    # 10/ Tableau d’affectation du résultat et des réserves (N-1)
    inv_tab_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 11/ Tableau des participations (filiales et entités associées)
    inv_tab_2_id = fields.Many2one('finn.liasse.fiscale.report')

    # 12/ Commissions et courtages, redevances, honoraires, sous-traitance, rémunérations diverses et frais de siège
    inv_commission_1_id = fields.Many2one('finn.liasse.fiscale.report')

    # 13/ Taxe sur l’activité professionnelle
    inv_commission_2_id = fields.Many2one('finn.liasse.fiscale.report')

    