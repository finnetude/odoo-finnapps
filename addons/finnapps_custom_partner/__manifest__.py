# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Custom Partner",
    'summary': """ Résumé du module""",
    'description' : "RESUME DU MODULE QUI N'apparais que sur l'installation de odoo",
    'version': '17.0.1.0',
    'category': 'Sales/CRM',
#
    'company': 'Finnetude',
    'author' : 'Finnetude',
    'maintainer': 'Finnetude',
    # 'support' : "ADRESSE MAIL POUR LES RECLAMATIONS",
    'website' : "http://www.finnetude.net/",
    'contributors' : [
    ],
#
    "license": "LGPL-3",
    "price": 0.0,
    "currency": 'EUR',
    # 'live_test_url' : "LIEN VERS FORMULAIRE POUR CREATION DE BASES TEST PROPRE A LA VERSION DU MODULE",
    'images' : ['images/banner.gif'],
#
    'depends' : [
            'base',
            'account',
    ],
#
    'data': [
        'views/res_partner.xml',
    ],
#    
#    'demo' : [
#        "DONNEES DE DEMONSTRATION"
#    ],
#    
#    'external_dependencies' : 'DEPENDANCES EXTERNES',
#    
    # 'sequence': 1,
    'installable': True,
    'auto_install': False,
    "application": False,
}
