# -*- coding: utf-8 -*-
{
    'name': "Primes et Avantages, Paie - Algérie",
    'summary': """ Ajouter les avantages d'un employé pour la paie """,
    'description': """ Ajouter les avantages d'un employé pour la paie  """,
    'version'       : "17.0.1.0",
    'category'      : "Human Resources/Employees",


    "contributors": [
    ],
    
    'sequence': 1,
    
    'company'       : 'Finnetude',
    'author'        : 'Finnetude',
    'maintainer'    : 'Finnetude',

    'website': "https://www.finnetude.com/",
    'support' : "support@finnetude.com",
    'live_test_url' : "https://www.finnetude.com/",

    'depends': [
        'finnapps_hr_payroll_dz',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',

        'data/cron.xml',

        'views/finn_hr_bonuse_advantage.xml',
        'views/finn_hr_lot_advantage.xml',
        'views/hr_contract.xml',
        'views/menuitems.xml',
    ],

    'images': ['images/banner.gif'],

    'license'       : "LGPL-3",
    'price'         : "55",
    'currency'      : 'Eur',
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
