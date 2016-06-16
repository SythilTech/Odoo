# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request

class TwilioController(http.Controller):

    @http.route('/sms/twilio/receipt', type="http", auth="public", csrf=False)
    def sms_twilio_receipt(self, **kwargs):
        """Update the state of a sms message, don't trust the posted data"""
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        request.env['sms.gateway.twilio'].sudo().delivary_receipt(values['AccountSid'], values['MessageSid'])
        
        return "<Response></Response>"
        
    @http.route('/sms/twilio/receive', type="http", auth="public", csrf=False)
    def sms_twilio_receive(self, **kwargs):
        """Fetch the new message directly from Twilio, don't trust posted data"""
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        
        twilio_account = request.env['sms.account'].sudo().search([('twilio_account_sid','=', values['AccountSid'])])
        request.env['sms.gateway.twilio'].sudo().check_messages(twilio_account.id, values['MessageSid'])
        
        return "<Response></Response>"