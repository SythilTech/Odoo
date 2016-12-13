# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsitePosOrder(models.Model):

    _name = "website.pos.order"

    state = fields.Selection([('draft','Draft'),('finished','Finished')], string="State")
    type = fields.Selection([('delivery','Delivery'), ('pickup','Pick-up')], string="Type")
    line_ids = fields.One2many('website.pos.order.line', 'wpo_id', string="Lines")
    
class WebsitePosOrderLine(models.Model):

    _name = "website.pos.order.line"

    wpo_id = fields.Many2one('website.pos.order', string="Restaurant POS Order")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Integer(string="Quantity")