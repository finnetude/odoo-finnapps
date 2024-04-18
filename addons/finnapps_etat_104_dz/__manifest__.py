# -*- coding: utf-8 -*
{
    'name': "Rapports de comptabilité - État 104 des clients",
    'summary': "Édition et impression de rapport état 104 des clients",
    'description': "Édition et impression de rapport état 104 des clients",


    'version': '17.0.1.0',
    'category': 'Accounting',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'support' : "support@finnetude.com",
    'website'     : "https://www.finnetude.com",

    "license": "OPL-1",
    "price": "82.49",
    "currency": 'EUR',
    'live_test_url': "https://www.finnetude.com",

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
       
        # Etat 104
        'reports/etat_104_report_format.xml',
        'reports/etat_104_report.xml',
        'wizards/finn_etat_104.xml',

        'views/menu_items.xml',
        
        'security/ir.model.access.csv',
    ],

    'images' : ['images/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application': True,
}
