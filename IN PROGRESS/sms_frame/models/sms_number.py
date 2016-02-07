# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SmsNumber(models.Model):

    _name = "sms.number"
    
    name = fields.Char(string="Name") 
    mobile_number = fields.Char(string="Mobile Number")
    account_id = fields.Many2one('sms.accounts', string="Account")