# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Livre Des Tiers Valorisé",
    'summary': """ Gestion des soldes clients """,
    'description': """ Gestion des soldes clients """,

    'version'     : "17.0.1.0",
    'category': 'Accounting/Accounting',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',



    'website': "https://www.finnetude.com/",
    'support' : "support@finnetude.com",
    'live_test_url' : "https://www.finnetude.com",


    "contributors": [
    ],

    'license': "LGPL-3",
    "price": 55,
    "currency": 'EUR',


    'depends': [
            'base',
            'web',
            'stock',
            'base_setup',
            'account',
            
            
    ],
    'demo': [
        'data/mail_template.xml',
    ],

    'data': [
        'data/accounting_group.xml',
        'security/ir.model.access.csv',

        'views/account_move_views.xml',
        'views/res_partner_view.xml',

        'reports/report_call.xml',
        'reports/report_solde_tiers.xml',
        'reports/report_solde_tiers_all.xml',

        'wizard/finn_imprimer_rapport.xml',

    ],

    'images': ['images/banner.gif'],

    

    'installable': True,
    'auto_install': False,
    "application":False,
}
