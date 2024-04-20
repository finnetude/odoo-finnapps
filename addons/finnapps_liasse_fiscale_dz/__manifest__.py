# -*- coding: utf-8 -*
{
    'name': "Rapports de comptabilité - Liasse Fiscale - Algérie",
    'summary': "Générer et imprimer les rapports liasse fiscale après Calcul relatifs à la comptabilité Algérienne",
    'description': "Générer et imprimer les rapports liasse fiscale après Calcul relatifs à la comptabilité Algérienne",
    'version': '17.0.1.0',
    'category': 'Accounting/accounting',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'support' : "support@finnetude.com",
    'website'     : "https://www.finnetude.com",

    "license": "OPL-1",
    "price": "274.98",
    "currency": 'EUR',
    'live_test_url': "https://www.finnetude.com/",

    "contributors": [
    ],
    
    'sequence': 1,

    'depends': [
        'base',
        'account',
        'finnapps_invoicing_dz',
        'finnapps_account_fiscalyear',
        'web',
    ],

    

    'data': [
        'data/finn_liasse_fiscale_type_data.xml',

        'views/finn_liasse_fiscale_type.xml',
        'views/finn_liasse_fiscale_report.xml',
        'views/finn_liasse_fiscale.xml',
        
        'reports/paper_format.xml',
        'reports/header_footer.xml',

        'reports/bilan_actif/bilan_actif_data.xml',
        'reports/bilan_actif/bilan_actif_view.xml',
        'reports/bilan_actif/bilan_actif_report.xml',

        'reports/bilan_passif/bilan_passif_data.xml',
        'reports/bilan_passif/bilan_passif_view.xml',
        'reports/bilan_passif/bilan_passif_report.xml',

        'reports/compte_resultat/compte_resultat_data.xml',
        'reports/compte_resultat/compte_resultat_view.xml',
        'reports/compte_resultat/compte_resultat_report.xml',

        'reports/tableau_flux_tresorerie/tableau_flux_tresorerie_data.xml',
        'reports/tableau_flux_tresorerie/tableau_flux_tresorerie_view.xml',
        'reports/tableau_flux_tresorerie/tresorerie_report.xml',

        'reports/stock/stock_data.xml',
        'reports/stock/stock_view.xml',
        'reports/stock/stock_report.xml',

        'reports/charge/charge_data.xml',
        'reports/charge/charge_view.xml',
        'reports/charge/charge_report.xml',

        'reports/amo_inv/amo_inv_data.xml',
        'reports/amo_inv/amo_inv_view.xml',
        'reports/amo_inv/amo_inv_report.xml',

        'reports/cess_prov/cess_prov_data.xml',
        'reports/cess_prov/cess_prov_view.xml',
        'reports/cess_prov/cess_prov_report.xml',

        'reports/perte_val/perte_val_data.xml',
        'reports/perte_val/perte_val_view.xml',
        'reports/perte_val/perte_val_report.xml',

        'reports/result/result_data.xml',
        'reports/result/result_view.xml',
        'reports/result/result_report.xml',

        'reports/tab/tab_data.xml',
        'reports/tab/tab_view.xml',
        'reports/tab/tab_report.xml',

        'reports/commission/commission_data.xml',
        'reports/commission/commission_view.xml',
        'reports/commission/commission_report.xml',

        

        # RAPPORT COMPLET
        'reports/multi_reports.xml',

        'views/menu_items.xml',
        
        'security/ir.model.access.csv',
        'security/security_rules.xml',
    ],

    'images'       : [
        'images/banner.gif'
    ],


    'installable': True,
    'auto_install': False,
    'application': True,
}
