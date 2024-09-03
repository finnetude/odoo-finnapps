# -*- coding : utf-8 -*-
{
    "name":"Ordres de virments bancaires - Fournisseurs",
    "description":"Générer les ordres de virments bancaires",
    "summary":"Générer les ordres de virments bancaires",


    'category': 'Accounting',
    'version': '17.0.1.0',


    'author': 'Finnetude',
    'website': 'https://www.finnetude.com',

    "license": "LGPL-3",
    "price": 75.00,
    "currency": 'EUR',




    "contributors": [
        

    ],

    'sequence': 1,


    'depends': [
        'base',
        'mail',
        'contacts',
    ],

    


    "data":[


        'security/access_group.xml',
        'security/access_rule.xml',
        'security/ir.model.access.csv',


        'wizards/finn_transfer_order_beneficiary.xml',


        'views/finn_transfer_order_line.xml',
        'views/finn_transfer_order.xml',
        'views/menu_items.xml',
        ],

    'images': [],





    'images': ['images/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application': True,
}


