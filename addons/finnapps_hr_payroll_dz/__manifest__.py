# -*- coding: utf-8 -*-
{
    'name': "Paie - Algérie",
    'summary': """ Intégration de la paie en fonction des réglementations algérienne """,

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
        'account',
        'finnapps_hr_dz',
        'finnapps_custom_employee',
        'finnapps_account_account_dz',
        'hr_contract',
        'hr_holidays',
    ],
    
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
        'security/security.xml',

        'data/hr_payroll_sequence.xml',
        'data/hr_payroll_leave_type.xml',
        'data/cron_functions.xml',
        'data/data_create_function.xml',

        'wizards/finn_hr_payroll_payslips_by_employees_views.xml',
        'views/hr_contract_views.xml',
        'views/finn_hr_salary_rule_views.xml',
        'views/finn_hr_payslip_views.xml',
        'views/finn_hr_payslip_run_view.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'reports/report_payslip_templates.xml',


        'views/hr_leave.xml',
        'views/hr_leave_type.xml',
        'views/finn_refund_tree_form.xml',
        'views/finn_hr_annual_leave.xml',
        'views/finn_hr_annual_leave_line.xml',
        'views/menu_item.xml',
        'views/account_journal.xml',

        'reports/employee_payslip_reports.xml',
        'reports/report_fiche_paie_individuel.xml',
        'reports/report_custom.xml',
        
        'reports/actions_reports_payroll.xml',
        'wizards/finn_hr_payslip_input_regul.xml',
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
