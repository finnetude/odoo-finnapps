# -*- coding: utf-8 -*-

{
    'name': "Code d'activité - Algérie",
    'description': """ Intégration des codes d'activité algériens. """,
    'summary': """ Intégration des codes d'activité algériens. """,


    'category': 'Accounting/accounting',
    'version': '17.0.1.0',

    "contributors": [
      
    ],

    'sequence': 1,

    
    'author': 'Finnetude',
    'website': 'https://www.finnetude.com',
    'live_test_url':"https://www.finnetude.com",

    "license": "LGPL-3",
    "price": 30,
    "currency": 'EUR',


    
    'depends': [
        'finnapps_invoicing_dz',
    ],

    'data': [
      
        'data/activity_code_data.xml',

    ],


    'images': ['images/banner.gif'],
   
    'installable': True,
    'auto_install': False,
    'application':False,
}
