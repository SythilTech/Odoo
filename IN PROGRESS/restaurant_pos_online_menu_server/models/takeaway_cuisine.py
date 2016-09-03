from openerp import models, fields, api

class TakeawayCuisine(models.Model):

    _name = "takeaway.cuisine"
    
    name = fields.Char(string='Cuisine Name')            