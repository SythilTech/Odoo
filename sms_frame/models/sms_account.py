# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SmsAccount(models.Model):

    _name = "sms.account"
    
    name = fields.Char(string='Account Name', required=True)
    account_gateway_id = fields.Many2one('sms.gateway', string="Account Gateway", required=True)
    gateway_model = fields.Char(string="Gateway Model", related="account_gateway_id.gateway_model_name")

    def send_message(self, from_number, to_number, sms_content, my_model_name='', my_record_id=0, media=None):
        """Send a message from this account"""
        return self.env[self.gateway_model].send_message(self.id, from_number, to_number, sms_content, my_model_name, my_record_id, media)
        

    @api.model
    def check_all_messages(self):
        """Check for any messages that might have been missed during server downtime"""
        my_accounts = self.env['sms.account'].search([])
        for sms_account in my_accounts:
            self.env[sms_account.account_gateway_id.gateway_model_name].check_messages(sms_account.id)