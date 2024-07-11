# -*- coding: utf-8 -*
{
    'name': "Paiement des fiches de paie",
    'summary': "Gestion des paiments des bulletins de paie",
    'description': "Gestion des paiments des bulletins de paie",


    'version': '17.0.1.0',
    'category'      : "Human Resources",

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'support' : "support@finnetude.com",
    'website'     : "https://www.finnetude.com",

    
    'live_test_url': "https://www.finnetude.com/shop",

    "contributors": [

    ],
    
    "license": "OPL-1",
    "price": "27.50",
    "currency": 'EUR',

    'sequence': 1,

    'depends': [
        'base',
        'finnapps_hr_payroll_dz'
       
    ],

  
    'data': [
        'security/ir.model.access.csv',
        'wizards/hr_payslip_payment_register.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_run.xml',
        

    ],

    'images': ['images/banner.gif'],


    'installable': True,
    'auto_install': False,
    'application': True,
}
