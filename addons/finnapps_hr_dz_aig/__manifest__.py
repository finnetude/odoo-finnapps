# -*- coding: utf-8 -*-
{
    'name': "Employés Aig - Algérie",
    'summary': """ Modification d'interface pour la gestion de la ressource humaine algérie """,
    'description': """ Modification d'interface pour la gestion de la ressource humaine algérie """,
    'version'       : "17.0.1.0",
    'category'      : "Human Resources/Employees",


    "contributors": [
    ],
    
    # 'sequence': 1,
    
    'company'       : 'Finnetude',
    'author'        : 'Finnetude',
    'maintainer'    : 'Finnetude',

    'website': "https://www.finnetude.com/",
    'support' : "support@finnetude.com",
    'live_test_url' : "https://www.finnetude.com/shop/employes-algerie-50?category=13#attr=111",

    'depends': [
        'contacts',
        'hr_contract',
        'account',
        'hr_holidays',
        'purchase',
        'finnapps_hr_dz'
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/hr_contract.xml',        
    ],

    'license'       : "LGPL-3",
    'price'         : "164.99",
    'currency'      : 'Eur',


    'images'        : [
        'images/banner.gif'
        ],

    
    'installable': True,
    'auto_install': False,
    'application': True,
}
