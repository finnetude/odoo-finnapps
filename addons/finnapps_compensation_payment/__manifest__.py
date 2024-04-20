# -*- coding               : utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name'       : "Invoice payment with vendor invoice",
    'summary'    : "Pouvoir payer une facture client par compensation avec facture fournisseur",
    'description': "Pouvoir payer une facture client par compensation avec facture fournisseur",
    'version'    : "17.0.1.0",
    'category': 'Accounting/Payment',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',
    'website'     : "http://www.finnetude.com",
    "contributors": [
    ],

    'license'      : "OPL-1",
    'price'        : "55",
    'currency'     : 'Eur',
    'live_test_url': "https://www.finnetude.com/",
    'images'       : [
        'images/banner.gif'
        ],

    'depends': ['base', 'account'],

    'data': [
        'data/accounting_group.xml',
        'wizard/finn_payment_wizard.xml',
        'views/invoice_inherited.xml',
        'views/journal.xml',
        
        'security/ir.model.access.csv',
        'data/sequences.xml',
    ],

   

    'sequence'    : 1,
    'installable' : True,
    'auto_install': False,
    "application" : False,
}
