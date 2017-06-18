# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
from datetime import datetime

class SMSAPiController(http.Controller):

    @http.route('/sms/api/send', type="http", auth="public", csrf=False)
    def sms_twilio_receipt(self, **kwargs):
        """Allows public users to posts smses if they have an API key"""
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        if 'Key' in values:        
            api_user = request.env['res.users'].search([('sms_rest_key','=', values['Key'] )])
        else:
            return "Missing 'Key'"
                
        if 'From' in values:
            from_mobile = values['From']
        else:
            return "Missing 'From'"

        if 'To' in values:
            to_mobile = values['To']
        else:
            return "Missing 'To'"

        if 'Body' in values:
            sms_body = values['Body']
        else:
            return "Missing 'Body'"
                
        my_sms = api_user.sms_account_id.send_message(values['From'], values['To'], values['Body'], 'res.partner', 0)
        
        #use the human readable error message if present
        error_message = ""
        if my_sms.human_read_error != "":
            error_message = my_sms.human_read_error
            return error_message
        else:
            error_message = my_sms.response_string
            
	my_model = request.env['ir.model'].search([('model','=','res.partner')])

	#for single smses we only record succesful sms, failed ones reopen the form with the error message
	sms_message = request.env['sms.message'].create({'record_id': 0,'model_id':my_model[0].id,'account_id':api_user.sms_account_id.id,'from_mobile':values['From'],'to_mobile':values['To'],'sms_content':values['Body'],'status_string':my_sms.response_string, 'direction':'O','message_date':datetime.utcnow(), 'status_code':my_sms.delivary_state, 'sms_gateway_message_id':my_sms.message_id, 'by_partner_id':api_user.partner_id.id})
	    	                
        return "Sent"
