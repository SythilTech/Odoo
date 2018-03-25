# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SmsNumber(models.Model):

    _name = "sms.number"
    
    name = fields.Char(string="Name", translate=True)
    mobile_number = fields.Char(string="Sender ID", help="A mobile phone number or a 1-11 character alphanumeric name")
    account_id = fields.Many2one('sms.account', string="Account")