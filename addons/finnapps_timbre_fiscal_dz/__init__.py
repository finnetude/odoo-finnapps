from . import models
import logging

import odoo
from odoo import api, SUPERUSER_ID

def post_init_hook(env):
    
    
    company = env.company
    
    if not company.sale_timbre  :
        
        account_id = env['account.account'].search([('code','=','101701')],limit=1).id

        account_purchase_id = env['account.account'].search([('code','=','101701')],limit=1).id

    company.write({
    		'tranche': 100.0,
			'prix': 1.0,
			'mnt_min': 500.0,
			'mnt_max': 1000000.0,
			'sale_timbre': account_id,
			'montant_en_lettre':True,
    		})