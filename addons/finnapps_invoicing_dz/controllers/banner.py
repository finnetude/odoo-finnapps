from odoo import http

class BannerCnrc(http.Controller):
	@http.route('/finnapps_invoicing_dz/banner_cnrc', type='json', auth="user")
	def banner(self):
		return {
			'html': """
				<ul style="background-color:#E6F1F4; height:100px;text-algin:center;padding-top:10px;">
					<li style="margin-left:40px;font-family: Arial, Helvetica, serif;font-size:15px;">Les activités règlementées sont représentées en couleur verte</li>
					<li style="margin-left:40px;font-family: Arial, Helvetica, sans-serif;font-size:15px;">Les activités non autorisées à l’inscription au registre du commerce sont représentées en couleur rouge</li>
				</ul>
			"""
		}
