{
    'name': 'Position Chatter', 
    'summary': 'Adds options for the chatter',
    'description': '''
        This module improves the design of the chatter and adds a user
        preference to set the position of the chatter in the form view.
    ''',
    'version': '17.0.1.0.1', 
    'category': 'Tools/UI',
    'license': 'LGPL-3', 
    'author': 'Finnetude',
    'website': 'http://www.finnetude.com',
    'live_test_url': 'http://www.finnetude.com',
    'contributors': [
    ],
    'depends': [
        'mail',
    ],
    'data': [
        'views/res_users.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'after', 
                'web/static/src/scss/primary_variables.scss', 
                'finnapps_chatter_position/static/src/scss/variables.scss'
            ),
        ],
        'web.assets_backend': [
            (
                'after', 
                'mail/static/src/views/web/form/form_compiler.js', 
                'finnapps_chatter_position/static/src/views/form/form_compiler.js'
            ),
            'finnapps_chatter_position/static/src/core/**/*.xml',
            'finnapps_chatter_position/static/src/core/**/*.scss',
        ],
    },
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
