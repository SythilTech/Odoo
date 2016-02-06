from openerp import models, fields, api

class SmsVerifiedNumber(models.Model):

    _name = "esms.verified.number"
    
    name = fields.Char(string="Name") 
    mobile_number = fields.Char(string="Mobile Number")
    account = fields.Many2one('sms.accounts', string="Account")