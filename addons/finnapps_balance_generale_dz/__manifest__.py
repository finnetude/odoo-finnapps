# -*- coding: utf-8 -*
{
    'name': "Rapports de comptabilité - Balance générale",
    'summary': "Édition et impression de rapport balance générale",
    'description': "Édition et impression de rapport balance générale",


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

    
    'live_test_url': "https://www.finnetude.com/",

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

    'images' : ['images/banner.gif'],


    'data': [
        
        'wizards/finn_balance_generale.xml',
        'reports/balance_generale_report.xml',
        'views/menu_items.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
