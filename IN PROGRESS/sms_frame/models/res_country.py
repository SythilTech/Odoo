# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResCountrySms(models.Model):

    _inherit = "res.country"
    
    mobile_prefix = fields.Char(string="Mobile Prefix")