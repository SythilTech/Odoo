# -*- coding: utf-8 -*-
from openerp import api, fields, models

class POSCategoryProducts(models.Model):

    _inherit = "pos.category"

    product_ids = fields.One2many('product.product', 'pos_categ_id', string="Products")