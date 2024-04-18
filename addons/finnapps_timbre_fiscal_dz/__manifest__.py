# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': "Droit de timbre client - Algérie",
    'summary': """Ce module permettant de gérer les droits de timbre pour les paiements en liquide sur les factures et les avoirs clients""",
    'description': """Gestion des droits de timbre client""",

    'version': '17.0.2.1',
    'category': 'Accounting/Accounting',


    "contributors": [
    ],
    
    
    
    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'website': 'http://www.finnetude.com',
    'support' : "support@finnetude.com",

    'live_test_url' : "https://www.finnetude.com",    


    "license": "OPL-1",
    "price": 55,
    "currency": 'EUR',


    'depends': [
        'base',
        'account'
    ],

    "sequence":1,

    'data': [
        'views/configuration_timbre.xml',
        'views/account_move.xml',
        'views/account_move_report.xml',
        'views/account_payment.xml',
        
        'security/ir.model.access.csv',

        'data/paymment_mode.xml',
        'data/accounting_group.xml',
    ],



    'images': ['images/banner.gif'],



    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': "post_init_hook",
}
