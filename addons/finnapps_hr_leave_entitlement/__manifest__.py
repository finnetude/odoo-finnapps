# -*- coding: utf-8 -*
{
    'name': "Titre de congé",
    'summary': "Générer et imprimer un titre de congé",
    'description': "Générer et imprimer un titre de congé",


    'version': '17.0.1.0',
    'category'      : "Human Resources",

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'website'     : "https://www.finnetude.net",

    
    "contributors": [

    ],
    
    "license": "OPL-1",
    "price": "27.50",
    "currency": 'EUR',

    'sequence': 1,

    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_holidays',

       
    ],

  
    'data': [
        'security/ir.model.access.csv',
        'wizards/hr_leave_entitlement.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave.xml',

        'reports/action_report.xml',
        'reports/format_paper.xml',
        'reports/layout.xml',
        'reports/leave_entitlement_report.xml',


    ],

    'images': ['images/banner.gif'],

    'installable': True,
    'auto_install': False,
    'application': True,
}
