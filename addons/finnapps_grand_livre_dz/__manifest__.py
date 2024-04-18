{
    'name': "Rapports de comptabilité - Grand livre",
    'summary': "Édition et impression de rapport grand livre",
    'description': "Édition et impression de rapport grand livre",


    'version': '17.0.1.0',
    'category': 'Accounting',

    'company'     : 'Finnetude',
    'author'      : 'Finnetude',
    'maintainer'  : 'Finnetude',

    'support' : "support@finnetude.com",
    'website'     : "https://www.finnetude.com",

    
    'live_test_url': "https://www.finnetude.com",

    "contributors": [
    ],
    'sequence': 1,

    'depends': [
        'base',
        'account',
        'finnapps_invoicing_dz',
        'finnapps_account_account_dz',
        'finnapps_account_fiscalyear',
        'web',
    ],

   

    'data': [
        
        'wizards/finn_grand_livre.xml',
        'reports/mise_en_page.xml',
        'reports/grand_livre_report.xml',

        'views/menu_items.xml',
        
        'security/ir.model.access.csv',
    ],


    'images'       : [
        'images/banner.gif'
    ],


    'license'       : "LGPL-3",
    'price'         : "82.49",
    'currency'      : 'Eur',

    'installable': True,
    'auto_install': False,
    'application': True,
}
