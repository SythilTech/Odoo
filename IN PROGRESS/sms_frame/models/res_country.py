from openerp import models, fields, api

class ResCountrySms(models.Model):

    _inherit = "res.country"
    
    mobile_prefix = fields.Char(string="Mobile Prefix")