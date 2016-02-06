from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class esms_accounts(models.Model):

    _name = "esms.accounts"
    _order ="priority asc"
    
    name = fields.Char(required=True, string='Account Name')
    account_gateway = fields.Many2one('esms.gateways', required=True)
    gateway_model = fields.Char(related="account_gateway.gateway_model_name")
    priority = fields.Integer(string="Priority", default="100")

    @api.model
    def check_all_messages(self):                
        my_accounts = self.env['esms.accounts'].search([('priority','>=',0)])        
        for sms_account in my_accounts:            
            self.env[sms_account.account_gateway.gateway_model_name].check_messages(sms_account.id)