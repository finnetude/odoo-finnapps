# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name'        : "Plan des comptes",
    'summary'     : "Structuration du plan comptable, Lecture des (Débit, Crédit, Solde) plus facile",
    'description' : "Structuration du plan comptable, Lecture des (Débit, Crédit, Solde) plus facile",
    'version'     : "17.0.1.0",
    'category': 'Accounting/Localizations',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',
    'website'     : "http://www.finnetude.net",

    "contributors": [
    ],

    'license'      : "OPL-1",
    'price'        : "82.49",
    'currency'     : 'Eur',
    'live_test_url': "https://www.finnetude.net/",

    
    'images'       : [
        'images/banner.gif'
        ],


    'depends': [
            'base',
            'finnapps_account_fiscalyear',
            'finnapps_invoicing_dz',
            'finnapps_account_account_dz',
            'mrp',
            'stock',
           # 'account',

    ],
    
    "data": {
        'views/finn_solde_compte.xml'
    },
    "assets": {
        "web.assets_backend": [
            "finnapps_solde_compte/static/src/js/finn_solde_compte.js",
            "finnapps_solde_compte/static/src/xml/finn_solde_compte.xml",
            "finnapps_solde_compte/static/src/css/scroll.css",

        ],
    },

    'installable': True,
    'auto_install': False,
    "application":True,
    "sequence":1,
}
