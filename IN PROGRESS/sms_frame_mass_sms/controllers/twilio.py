import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    @http.route('/sms/twilio/receipt', type="http", auth="public")
    def sms_twilio_receipt(self, **kwargs):
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        request.env['esms.twilio'].sudo().delivary_receipt(values['AccountSid'], values['MessageSid'])
        
        return "<Response></Response>"
        
    @http.route('/sms/twilio/receive', type="http", auth="public")
    def sms_twilio_receive(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        
        twilio_account = request.env['esms.accounts'].sudo().search([('twilio_account_sid','=', values['AccountSid'])])
        request.env['esms.twilio'].sudo().check_messages(twilio_account.id, values['MessageSid'])
        
        return "<Response></Response>"