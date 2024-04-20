# -*- coding: utf-8 -*-
{
    'name': "Droit de Timbre sur Facture et sur Paiement Fournisseur- Algérie",
    
    'summary': """ Gestion de droit de timbre sur les factures et les paiements fournisseur""",
    'description': """ Gestion de droit de timbre sur les factures et les paiements fournisseur""",



    'category': 'Accounting',
    'version': '17.0.1.1',


    "contributors": [
    ],
    'sequence': 1,


    
    
    'author': 'Finnetude',


    'website': 'https://www.finnetude.com/',
    'support'     : "support@finnetude.com",
    'live_test_url':"https://www.finnetude.com",

    "license": "LGPL-3",
    "price": 27.50,
    "currency": 'EUR',


    
    'depends': [
        'base',
        'finnapps_timbre_fiscal_dz',
    ],


    'data': [
        "data/timbre_journal.xml",
        "views/configuration_settings.xml",
        "views/account_move.xml",
        "views/account_payment.xml",
        "views/account_payment_register.xml",
        "views/account_journal.xml",
        

        
    ],


    'images': ['images/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application':False,
    'post_init_hook': "post_init_hook_t",
}
