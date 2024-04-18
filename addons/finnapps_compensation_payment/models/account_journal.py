from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountJournalInherited(models.Model):
	_inherit = 'account.journal'

	compensation_journal = fields.Boolean(
		string="Utiliser pour la compensation",
		default=False
		)

	# Fonction contrainte pour un journal unique de compensation
	@api.constrains("compensation_journal")
	def constraints_pour_paiement_compensation(self):
		if self.compensation_journal and self.env['account.journal'].search([('compensation_journal','=',True), ('id','!=',self.id)]):
			raise ValidationError('Utiliser pour la compensation ne doit être coché que sur un seul journal.')