# -*- coding: utf-8 -*-
{
    'name': "Auto Référencement Des Tiers",
    "summary": "Générer automatiquement un numéro propre aux clients et aux fournisseurs.",
    "description": "Génére automatiquement un numéro propre aux clients et aux fournisseurs.",
    'category': 'Sales/CRM',


    "contributors": [
        
],
    'sequence': 1,
    'version': '17.0.1.0',
    "license": "LGPL-3",
    'author': 'Finnetude',
    'website': "https://finnetude.com",
    "price": 0.0,
    "currency": 'EUR',
    'live_test_url': "https://www.finnetude.com",

    'depends': [
        'base',
        'account',
        'finnapps_custom_partner',
    ],
    'data': [
        'data/accounting_group.xml',
        'data/sequences.xml',
        'views/res_partner.xml',
    ],
    
    'images': ['static/description/banner.gif'],
        
    'installable': True,
    'auto_install': False,
    'application': False,
}