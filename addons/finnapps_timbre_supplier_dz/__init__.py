from . import models

import odoo
from odoo import api, SUPERUSER_ID

def post_init_hook_t(env):
    
    
    company = env.company
    
    if not company.purchase_offset_account:
        
        account_timbr = env['account.account'].search([('code','=','645700')],limit=1).id
           
  


    company.write({
    	
			'purchase_offset_account': account_timbr,

    		})
