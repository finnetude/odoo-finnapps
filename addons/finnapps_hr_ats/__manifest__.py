# -*- coding: utf-8 -*-
{
    'name': "Attestation de travail et de salaire (ATS) - Algérie",
    'summary': """ Édition et impression du rapport ATS de la CNAS """,
    'description': """ Édition et impression du rapport ATS de la CNAS """,

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

    'license'       : "LGPL-3",
    'price'         : "27.50",
    'currency'      : 'Eur',


    'images': ['images/banner.gif'],

    'depends': [
        'finnapps_hr_payroll_dz',
    ],
    
    'data': [
        'security/ir.model.access.csv',

        'views/finn_hr_ats.xml',
        'views/menuitems.xml',
        
        'reports/print_ats_report.xml',
        'reports/report_layout.xml',
        'reports/report_ats_recto.xml',
        'reports/report_ats_verso.xml',
        
    ],


    'installable': True,
    'auto_install': False,
    'application': True,
}
