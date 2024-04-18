# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Facture et Comptabilité - Algérie",
    'summary': """ Facture et comptabilité aux normes algériennes. """,

    'category': 'Accounting/Localizations/Account Charts',
    'version': '17.0.1.2',

    "contributors": [
    ],
    'sequence': 1,

    'author': 'Finnetude',
    'website': 'https://www.finnetude.com',
    'live_test_url':"https://www.finnetude.com",

    "license": "LGPL-3",
    "price": 50.0,
    "currency": 'EUR',
    
    'depends': [
        'l10n_dz',
        'sale_management',
        'contacts',

    ],

    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',

        'views/finn_activity_code.xml',
        'views/finn_forme_juridique.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/configuration_settings.xml',
        'views/menuitems.xml',
        
        'data/finn_forme_juridique_create.xml',
        'data/group_account_readonly.xml',
        'data/res_country_dz.xml',

        'reports/account_invoice_report.xml',
        'reports/sale_order_report.xml',
    ],

    'images': ['images/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application':False,
}
