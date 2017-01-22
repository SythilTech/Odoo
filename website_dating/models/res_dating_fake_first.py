# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResDatingFakeFirst(models.Model):

    _name = "res.dating.fake.first"
    
    name = fields.Char(string='First Name')
    gender_id = fields.Many2one('res.partner.gender', string="Gender")
    amount = fields.Integer(string="Amount")