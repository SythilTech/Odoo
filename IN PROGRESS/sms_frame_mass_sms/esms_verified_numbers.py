from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_verified_numbers(models.Model):

    _name = "esms.verified.numbers"
    
    name = fields.Char(string="Name") 
    mobile_number = fields.Char(string="Mobile Number")
    account_id = fields.Many2one('esms.accounts', string="Account")
    mobile_verified = fields.Boolean(readonly="True", string="Can receive SMS", help="Verified if the number has functioning send and receive functionality", compute="_mobile_verify")
    
    @api.one
    @api.depends('mobile_number')
    def _mobile_verify(self):
        if self.env['esms.history'].search_count([('to_mobile','=',self.mobile_number), ('direction','=','I')]) > 0:
            self.mobile_verified = True
            
    
    @api.one
    def send_mobile_verify(self):
        #Send sms from this number to this number
        gateway_model = self.account_id.account_gateway.gateway_model_name
	my_sms = self.env[gateway_model].send_message(self.account_id.id, self.mobile_number, self.mobile_number, "gFrqjUVbfWpUcJL", "esms.verified.numbers", self.id, "mobile_number")
