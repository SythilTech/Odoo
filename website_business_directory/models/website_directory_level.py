# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteDirectoryLevel(models.Model):

    _name = "website.directory.level"

    name = fields.Char(string="Name")
    billing_plan = fields.Many2one('website.directory.billingplan', string="Billing Plan")
    category_limit = fields.Integer(string="Category Limit")