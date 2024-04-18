from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import date


class FinnLotDeclarationCotisation(models.Model):
    _name = "finn.lot.declaration.cotisation"
    _description = 'Lot de déclaration de cotisation'

    name = fields.Char('Nom', readonly=True, required=True, copy=False, compute="name_cotisation")
    creation_date = fields.Date('Date de création', default = date.today())
    company_id = fields.Many2one(
        'res.company',
        'Société', 
        default=lambda self: self.env.company,
        readonly=True
    )

    year = fields.Integer('Année actuelle', default=date.today().year)

    month = fields.Selection(
        [('1', 'Janvier'),
         ('2', 'Février'),
         ('3', 'Mars'),
         ('4', 'Avril'),
         ('5', 'Mai'),
         ('6', 'Juin'),
         ('7', 'Juillet'),
         ('8', 'Août'),
         ('9', 'Septembre'),
         ('10', 'Octobre'),
         ('11', 'Novembre'),
         ('12', 'Décembre')],
        'Mois'
    )

    trimester = fields.Selection(
        [('1', 'Premier trimestre'),
         ('2', 'Deuxième trimestre'),
         ('3', 'Troisième trimestre'),
         ('4', 'Quatrième trimestre')],
        'Trimestre',readonly=True,
        compute="_compute_trimester",
        store=True,
    )
    
    declaration_cotisation_ids = fields.One2many(
        'finn.declaration.cotisation', 
        'lot_declaration_cotisation_id', 
        string='Déclaration des cotisations'
    )

    note  = fields.Text('Note')

    @api.depends('month')
    def _compute_trimester(self):
        for record in self:
            if record.month == '3':
                record.trimester = '1'
            elif record.month == '6':
                record.trimester = '2'
            elif record.month == '9':
                record.trimester = '3'
            elif record.month == '12':
                record.trimester = '4'
            else:
                record.trimester = ''
                
    @api.depends('month','year')
    def name_cotisation(self): 
        for record in self:
            month = record._fields['month'].selection
            code_dict = dict(month)
            month = code_dict.get(record.month)
            year = record.year if record.year else ''
            month = month if month else ''
            record.name ="Lot de déclaration des cotisations %s %s" % (month,year)

    #generate the lines of Contribution declaration batch
    def generate(self):

        self.declaration_cotisation_ids.unlink()

        #get the agnecies regesterd in the company
        declaration_lines = []
        agencies = self.env['hr.employee'].search([]).mapped('payment_center_id')

        #create the declaration lines per the cnas declaration mode
        #and calculate the "cotisation lines"
        if agencies:
            for agency in agencies:
                if self.month not in ['3','6','9','12'] and agency.declaration_type == '2':
                    continue
                    
                declaration_lines.append((0,0,{
                        'month':self.month, 
                        'trimester':self.trimester,
                        'periode':agency.declaration_type,
                        'agency_id':agency.parent_id.id, 
                        'payment_center_id': agency.id
                    }))
                
            self.write({'declaration_cotisation_ids':declaration_lines})

            for rec in self.declaration_cotisation_ids:
                rec.calculate()
        else:
            raise models.ValidationError("Remplir les agences cnas au niveau de société")
