# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCountrySms(models.Model):

    _inherit = "res.country"
    
    mobile_prefix = fields.Char(string="Mobile Prefix")