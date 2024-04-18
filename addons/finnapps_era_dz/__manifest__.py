# -*- coding: utf-8 -*

{
    'name': "Rapports de comptabilité - État récapitulatif annuel - Algérie",
    'summary': "Impressions de rapport ERA après Calcul relatifs à la comptabilité Algérienne",
    'description': "Impression de rapport ERA après Calcul relatifs à la comptabilité Algérienne",



    'version': '17.0.1.0',
    'category': 'Accounting',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',


    'support' : "support@finnetude.com",
    'website'     : "https://www.finnetude.com",
    'live_test_url': "https://www.finnetude.com",

    "license": "OPL-1",
    "price": "27.50",
    "currency": 'EUR',
    



    "contributors": [
    ],
    'sequence': 1,
    

    'depends': [
        'base',
        'account',
        'finnapps_invoicing_dz',
        'finnapps_account_account_dz',
        'finnapps_account_fiscalyear',
        'web',


    ],
    'data': [
        

       
        'views/finn_summary_statement_config_view.xml',
        'wizards/finn_summary_statement_annual.xml',
        'data/data_sumstate_config.xml',
        'reports/summary_statement_annual_report.xml',

        'security/ir.model.access.csv',
        'security/security_rules.xml',
    ],
    'images': ['images/banner.gif'],


    'installable': True,
    'auto_install': False,
    'application': True,
}
