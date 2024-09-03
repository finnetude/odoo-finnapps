# -*- coding : utf-8 -*-
{
    "name":"Ordres de virments bancaires - Salariés",
    "description":"Générer les ordres de virments bancaires des salariés",
    "summary":"Générer les ordres de virments bancaires des salariés",





    'version'       : "17.0.1.0",
    'category'      : "Human Resources/Employees",



    "contributors": [
        

    ],


    'company'       : 'Finnetude',
    'author'        : 'Finnetude',
    'maintainer'    : 'Finnetude',

    'website': "https://www.finnetude.com/",


    'sequence': 1,


    'depends': [
        'base',
        'finnapps_bank_transfer_order',
        'finnapps_hr_payroll_dz',
        
    ],

    


    "data":[

        
        'security/ir.model.access.csv',
        'wizards/finn_get_employees.xml',
        'views/finn_transfer_order.xml',

        ],

    'license'       : "LGPL-3",
    'price'         : "30.00",
    'currency'      : 'Eur',


    'images': ['images/banner.gif'],


    'installable': True,
    'auto_install': False,
    'application': True,
}


