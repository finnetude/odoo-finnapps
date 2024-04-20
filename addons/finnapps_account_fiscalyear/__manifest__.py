# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Fiscal year and periods",


    'version': '17.0.1.1',
    'category': 'Accounting/Accounting',



   
    'author': 'Finnetude',
    'website': 'http://www.finnetude.com',
    'live_test_url': "https://www.finnetude.com",

    "license": "OPL-1",
    "price": 55,
    "currency": 'EUR',
    
    "contributors": [
    ],
    'depends': [
            'base',
            'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',


        'views/periode.xml',
        'views/exercice.xml',
        'views/account_move.xml',

        'wizards/close_periode.xml',
        'wizards/message_error.xml',
        'wizards/generer_ecriture.xml',
        'wizards/lettrer_ecriture.xml',
        'wizards/annuler_ecriture.xml',
        'wizards/fermer_exercice.xml',
        'wizards/generer_exercice.xml',

        

        'data/accounting_group.xml',
        'data/cron_remplir_periode.xml',
    ],
    'images': ['images/baneer.gif'],
    'installable': True,
    'auto_install': False,
    "application": True,
}
