# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResDatingFakeFirst(models.Model):

    _name = "res.dating.fake.first"
    
    name = fields.Char(string='First Name')
    gender = fields.Char(string="Gender")
    amount = fields.Integer(string="Amount")