# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Comptes comptables - Algérie",
    'summary': """ Comptes comptables algériens. """,

    'category': 'Accounting/Localizations/Account Charts',
    'version': '17.0.1.0',

    "contributors": [
    ],
    'sequence': 1,

    'author': 'Finnetude',
    'website': 'https://www.finnetude.com',
    'live_test_url':"https://www.finnetude.com",

    "license": "LGPL-3",
    "price": 10.0,
    "currency": 'EUR',
    
    'depends': [
        'base',
        'account',
    ],

    'data': [
        
        'data/account_account.xml',

       
    ],

    'images': ['images/banner.gif'],


    'installable': True,
    'auto_install': False,
    'application':False,
}
