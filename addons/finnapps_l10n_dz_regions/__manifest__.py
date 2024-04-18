# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': '58 Wilayas, Communes, Localités et Codes Postaux - Algérie',
    'summary' : "Gestion par base de données relationnelles des adresses de vos contacts localisé en Algérie",
    'description' : "Gestion par base de données relationnelles des adresses de vos contacts localisé en Algérie",
    'version': '17.0.1.0',
    'category': 'Sales/CRM',

    'company': 'Finnetude',
    'author' : 'Finnetude',
    'maintainer': 'Finnetude',

    
    'support' : "support@finnetude.com",
    'website' : "http://www.finnetude.com",
    'live_test_url' : "https://www.finnetude.com/",

    "contributors": [

    ],

    'license' : "OPL-1",
    'price' : "40",
    'currency' : 'Eur',


    'images' : ['images/banner.gif'],

    'depends': [
        'base',
        'contacts',
    ],
    
    'data': [
        'security/ir.model.access.csv',

        'data/res_country_state.xml',
        'data/res_country_commune.xml',
        'data/res_country_localite.xml',

        'views/res_country.xml',
        'views/res_bank.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
    ],
    
    'demo' : [
    ],
    
    'installable': True,
    'auto_install': False,
    "application": False,
}
