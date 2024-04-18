# -*- coding: utf-8 -*-
{   
    'name': "Rapports CNAS - Algérie",
    'summary': """ Implémentation des rapports CNAS """,

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
    'live_test_url' : "https://www.finnetude.com",

    'depends': [
        'base',
        'finnapps_hr_payroll_dz',
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'wizards/finn_employee_list.xml',
        
        'reports/custom_header.xml',
        'reports/report_template.xml',
        'reports/format_report.xml',
        'reports/report.xml',
        'reports/report_das.xml',
        'views/finn_declaration_cotisation.xml',
        'views/finn_declaration_das.xml',
        'views/finn_lot_declaration_cotisation.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/finn_activity_code.xml',
        'views/menu_item.xml',
    ],

    'images'       : [
        'images/banner.gif'
    ],


    'license'       : "LGPL-3",
    'price'         : "109.99",
    'currency'      : 'Eur',

    'installable': True,
    'auto_install': False,
    "application": True,


}
