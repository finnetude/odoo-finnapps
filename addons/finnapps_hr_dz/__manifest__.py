# -*- coding: utf-8 -*-
{
    'name': "Employés - Algérie",
    'summary': """ Modification d'interface pour la gestion de la ressource humaine algérie """,
    'description': """ Modification d'interface pour la gestion de la ressource humaine algérie """,
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
    'live_test_url' : "https://www.finnetude.com/shop/employes-algerie-50?category=13#attr=111",

    'depends': [
        'contacts',
        'hr_contract',
        'account',
        'hr_holidays',
    ],
    
    'data': [
        'data/sequences.xml',

        'data/resource_data.xml',
        
        'data/hr_contract_anem.xml',
        'data/hr_contract.xml',

        'data/resource_calendar_attendance.xml',
        'data/functions.xml',

        'views/res_partner.xml',
        'views/hr_employee.xml',
        'views/res_company.xml',
        'views/hr_contract.xml',
        'views/iep.xml',
        'views/calendar.xml',

        'reports/employee_certificats_reports.xml',
        'reports/format_paper.xml',
        'reports/report_certificate.xml',
        'reports/report_attesation.xml',

        'wizards/hr_contract_report.xml',
        
        'security/ir.model.access.csv',
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
