# -*- coding: utf-8 -*-
{
    'name': "Rapports comptables de la paie - Algérie",
    'description': """ Intégration des rapports comptables liées aux ressources humaine """,
    'summary': """ Intégration des rapports comptables liées aux ressources humaine """,



    'version'       : "17.0.1.1",
    'category'      : "Human Resources/Employees",


    "contributors": [
    ],
    
    'sequence': 1,

    'company'       : 'Finnetude',
    'author'        : 'Finnetude',
    'maintainer'    : 'Finnetude',

    
    'website': "https://www.finnetude.com/",
    'support' : "support@finnetude.com",


    'depends': [
        'base',
        'finnapps_hr_payroll_dz',
    ],
    
    
    'data': [
        'security/ir.model.access.csv',
        
        'reports/report_paie_custom_header.xml',
        'reports/report_custom_footer.xml',
        'reports/livre_paie_format_paper.xml',
        'reports/employee_payslip_reports.xml',
        'reports/report_livre_de_paie.xml',
        'reports/report_etat_prestation.xml',
        'reports/report_declaration_fiscales.xml',
        'reports/report_ventilation_comptable.xml',
        


       
        'views/finn_hr_fiscal.xml',
        
        'views/finn_ventilation_comptable_view.xml',
        'views/finn_hr_payroll_book.xml',
        'views/finn_hr_payroll_book_total.xml',
        
        'data/sequence_fiscal.xml',


    
    ],


    'images': ['images/banner.gif'],
    
    'license'       : "LGPL-3",
    'price'         : "137.49",
    'currency'      : 'Eur',



    
    'installable': True,
    'auto_install': False,
    'application': True,
}
