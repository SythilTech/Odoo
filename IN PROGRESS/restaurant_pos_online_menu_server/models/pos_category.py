from openerp import models, fields, api

class PosCategoryTakeaway(models.Model):

    _inherit = "pos.category"
    
    product_ids = fields.One2many('product.template', 'pos_categ_id', string="Products")