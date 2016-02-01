# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResDatingFakeLast(models.Model):

    _name = "res.dating.fake.last"
    
    name = fields.Char(string='First Name')
    amount = fields.Integer(string="Amount")