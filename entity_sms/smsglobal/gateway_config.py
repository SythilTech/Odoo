from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class sms_response():
     delivary_state = ""
     response_string = ""
     human_read_error = ""
     message_id = ""

class smsglobal_core(models.Model):

    _name = "esms.smsglobal"
    
    api_url = fields.Char(string='API URL')
    
 
    def send_message(self, sms_gateway_id, from_number, to_number, sms_content, my_model_name='', my_record_id=0, my_field_name=''):
        sms_account = self.env['esms.accounts'].search([('id','=',sms_gateway_id)])
        
        #format the from number before sending
        format_from = from_number
        if " " in format_from: format_from.replace(" ", "")
        if "+" in format_from: format_from = format_from.replace("+", "")
        
        #format the to number before sending
        format_to = to_number
        if " " in format_to: format_to.replace(" ", "")
        if "+" in format_to: format_to = format_to.replace("+", "")
                
        #send the sms/mms
        smsglobal_url = "http://www.smsglobal.com/http-api.php?action=sendsms&user=" + str(sms_account.smsglobal_username) + "&password=" + str(sms_account.smsglobal_password) + "&from=" + str(format_from) + "&to=" + str(format_to) + "&text=" + str(sms_content)
	response_string = requests.get(smsglobal_url)
        
        #Analyse the reponse string and determine if it sent successfully other wise return a human readable error message   
        human_read_error = ""
        delivary_state = "failed"
        if response_string.text == "ERROR: 88":
	    human_read_error = "INSUFFICIENT CREDIT"
	elif "ERROR: 40" in response_string.text:
	    human_read_error = "BAD CREDENTIALS"
	elif "ERROR: 8" in response_string.text:
	    human_read_error = "Source or Destination number is not correctly formated"    
	elif "ERROR" in response_string.text:
	    human_read_error = "FAILED DELIVERY"
	else:
	    delivary_state = "successful"
       
        #The message id is important for delivary reports also set delivary_state=successful
	sms_gateway_message_id = response_string.text.split('SMSGlobalMsgID:')[1]    
                
        #send a repsonse back saying how the sending went
        my_sms_response = sms_response()
        my_sms_response.delivary_state = delivary_state
        my_sms_response.response_string = response_string.text
        my_sms_response.human_read_error = human_read_error
        my_sms_response.message_id = sms_gateway_message_id
        return my_sms_response


class smsglobal_conf(models.Model):

    _inherit = "esms.accounts"
    
    smsglobal_username = fields.Char(string='API Username')
    smsglobal_password = fields.Char(string='API Password')