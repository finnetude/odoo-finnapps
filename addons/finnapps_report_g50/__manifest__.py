# -*- coding: utf-8 -*-

{
    'name': "Rapport (d'impression) G50",
    'summary':'Pouvoir éditer et imprimer la déclaration G50',
    'description':'Pouvoir éditer et imprimer la déclaration G50',
    'version'    : "17.0.2.0",



    'author'      : "finnetude",
    'company'     : 'finnetude',
    'maintainer'  : 'finnetude',
    'category': 'Accounting/Localizations/Reporting',


    "contributors": [

    ],
    'sequence': 1,
    
    'website': "http: //www.finnetude.com/",
    'support' : "support@finnetude.com",
    'live_test_url' : "https://www.finnetude.com/",


    'depends': [
            'finnapps_account_fiscalyear',
            'finnapps_l10n_dz_regions',
            'finnapps_invoicing_dz',
            'account',
            'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/config_g50_ratio.xml',
        'data/config_g50.xml',
        'data/config_g50_line.xml',
        'data/config_g50_a_line.xml',
        'data/config_g50_ter_line.xml',

        'reports/paper_format.xml',
        'reports/g50_rapport.xml',

        'views/g50_config.xml',
        'views/g50_report.xml',
        'views/g50_report_line.xml',
        
        'views/menu_items.xml',
    ],

    'license'       : "LGPL-3",
    'price'         : "82.49",
    'currency'      : 'Eur',


    'images'        : [
        'images/banner.gif'
        ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
