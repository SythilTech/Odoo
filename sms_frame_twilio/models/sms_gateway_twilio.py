# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from lxml import etree

from openerp.http import request
from openerp import api, fields, models
from openerp.exceptions import UserError

class sms_response():
     delivary_state = ""
     response_string = ""
     human_read_error = ""
     message_id = ""

class SmsGatewayTwilio(models.Model):

    _name = "sms.gateway.twilio"
    _description = "Contains all the code relating to sending and receiving smses using the Twilio gateway"
    
    api_url = fields.Char(string='API URL')
    
    def send_message(self, sms_gateway_id, from_number, to_number, sms_content, my_model_name='', my_record_id=0):
        """Actual Sending of the sms"""
        sms_account = self.env['sms.account'].search([('id','=',sms_gateway_id)])
        
        #format the from number before sending
        format_from = from_number
        if " " in format_from: format_from.replace(" ", "")
        
        #format the to number before sending
        format_to = to_number
        if " " in format_to: format_to.replace(" ", "")        
        
        #send the sms/mms
        base_url = self.env['ir.config_parameter'].search([('key','=','web.base.url')])[0].value
        payload = {'From': str(format_from), 'To': str(format_to), 'Body': str(sms_content), 'StatusCallback': base_url + "/sms/twilio/receipt"}
        response_string = requests.post("https://api.twilio.com/2010-04-01/Accounts/" + str(sms_account.twilio_account_sid) + "/Messages", data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))

        #Analyse the reponse string and determine if it sent successfully other wise return a human readable error message   
        human_read_error = ""
        root = etree.fromstring(response_string.text.encode('utf-8'))
        my_elements_human = root.xpath('/TwilioResponse/RestException/Message')
        if len(my_elements_human) != 0:
	    human_read_error = my_elements_human[0].text
        
        #The message id is important for delivary reports also set delivary_state=successful
	sms_gateway_message_id = ""
	delivary_state = "failed"
	my_elements = root.xpath('//Sid')
	if len(my_elements) != 0:
	    sms_gateway_message_id = my_elements[0].text
            delivary_state = "successful"
        
        #send a repsonse back saying how the sending went
        my_sms_response = sms_response()
        my_sms_response.delivary_state = delivary_state
        my_sms_response.response_string = response_string.text
        my_sms_response.human_read_error = human_read_error
        my_sms_response.message_id = sms_gateway_message_id
        return my_sms_response

    def check_messages(self, account_id, message_id=""):
        """Checks for any new messages or if the message id is specified get only that message"""
        sms_account = self.env['sms.account'].browse(account_id)
        
        if message_id != "":
            payload = {}
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + sms_account.twilio_account_sid + "/Messages/" + message_id, data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
	    root = etree.fromstring(str(response_string.text.encode('utf-8')))
	    my_messages = root.xpath('//Message')
            sms_message = my_messages[0]
            #only get the inbound ones as we track the outbound ones back to a user profile
            if sms_message.xpath('//Direction')[0].text == "inbound":
                self._add_message(sms_message, account_id)
        else:
            #get a list of all new inbound message since the last check date
            payload = {}
            if sms_account.twilio_last_check_date != False:
                my_time = datetime.strptime(sms_account.twilio_last_check_date,'%Y-%m-%d %H:%M:%S')
                payload = {'DateSent>': str(my_time.strftime('%Y-%m-%d'))}
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + sms_account.twilio_account_sid + "/Messages", data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
            root = etree.fromstring(str(response_string.text.encode('utf-8')))
            
            
            #get all pages
            messages_tag = root.xpath('//Messages')
            
            
            num_pages = messages_tag[0].attrib['numpages']
            for sms_page in xrange(0, int(num_pages)):
                my_messages = messages_tag[0].xpath('//Message')
                for sms_message in my_messages:
                    
                    #only get the inbound ones as we track the outbound ones back to a user profile
                    if sms_message.find('Direction').text == "inbound":
                        self._add_message(sms_message, account_id)
                        
                #get the next page if there is one
                if sms_page < (int(num_pages) - 1):
                    response_string = requests.get("https://api.twilio.com" + messages_tag[0].attrib['nextpageuri'], data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
		    root = etree.fromstring(response_string.text.encode('utf-8'))
		    messages_tag = root.xpath('//Messages')
		
	
        sms_account.twilio_last_check_date = datetime.utcnow()
            
    def _add_message(self, sms_message, account_id):
        """Adds the new sms to the system"""       
        delivary_state = ""
	if sms_message.find('Status').text == "failed":
	    delivary_state = "failed"
        elif sms_message.find('Status').text == "sent":
	    delivary_state = "successful"
	elif sms_message.find('Status').text == "delivered":
	    delivary_state = "DELIVRD"
	elif sms_message.find('Status').text == "undelivered":
	    delivary_state = "UNDELIV"
	elif sms_message.find('Status').text == "received":
	    delivary_state = "RECEIVED"
	
        my_message = self.env['sms.message'].search([('sms_gateway_message_id','=', sms_message.find('Sid').text)])
        if len(my_message) == 0 and sms_message.find('Direction').text == "inbound":
	    
	    target = self.env['sms.message'].find_owner_model(my_message)
	    
	    model_id = self.env['ir.model'].search([('model','=', target['target_model'])])
	    
	    twilio_gateway_id = self.env['sms.gateway'].search([('gateway_model_name', '=', 'sms.gateway.twilio')])
	    	    
	    self.env[target['target_model']].search([('id','=', target['record_id'].id)]).message_post(body=sms_message.find('Body').text, subject="SMS Received")
	    	    
	    #Create the sms record in history
	    history_id = self.env['sms.message'].create({'account_id': account_id, 'status_code': "RECEIVED", 'from_mobile': sms_message.find('From').text, 'to_mobile': sms_message.find('To').text, 'sms_gateway_message_id': sms_message.find('Sid').text, 'sms_content': sms_message.find('Body').text, 'direction':'I', 'message_date':sms_message.find('DateUpdated').text, 'model_id':model_id.id, 'record_id':int(target['record_id'].id)})
                    
    def delivary_receipt(self, account_sid, message_id):
        """Updates the sms message when it is successfully received by the mobile phone"""
        my_account = self.env['sms.account'].search([('twilio_account_sid','=', account_sid)])[0]
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + my_account.twilio_account_sid + "/Messages/" + message_id, auth=(str(my_account.twilio_account_sid), str(my_account.twilio_auth_token)))
        root = etree.fromstring(str(response_string.text))
        
        
        #map the Twilio delivary code to the sms delivary states 
	delivary_state = ""
	if root.xpath('//Status')[0].text == "failed":
	    delivary_state = "failed"
	elif root.xpath('//Status')[0].text == "sent":
	    delivary_state = "successful"
	elif root.xpath('//Status')[0].text == "delivered":
	    delivary_state = "DELIVRD"
	elif root.xpath('//Status')[0].text == "undelivered":
	    delivary_state = "UNDELIV"
        
        my_message = self.env['sms.message'].search([('sms_gateway_message_id','=', message_id)])
        if len(my_message) > 0:
            my_message[0].status_code = delivary_state
            my_message[0].delivary_error_string = root.xpath('//ErrorMessage')[0].text        
            
class SmsAccountTwilio(models.Model):

    _inherit = "sms.account"
    _description = "Adds the Twilio specfic gateway settings to the sms gateway accounts"
    
    twilio_account_sid = fields.Char(string='Account SID')
    twilio_auth_token = fields.Char(string='Auth Token')
    twilio_last_check_date = fields.Datetime(string="Last Check Date")
    
    @api.one
    def twilio_quick_setup(self):
        """Configures your Twilio account so inbound messages point to your server, also adds mobile numbers to the system"""
	response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
        if response_string.status_code == 200:
            response_string_twilio_numbers = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/IncomingPhoneNumbers", auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
            
            #go through each twilio number in the account and set the the sms url
            root = etree.fromstring(str(response_string_twilio_numbers.text))
	    my_from_number_list = root.xpath('//IncomingPhoneNumber')
	    for my_from_number in my_from_number_list:
	        av_phone = my_from_number.xpath('//PhoneNumber')[0].text
	        sid = my_from_number.xpath('//Sid')[0].text
	        
                    
                #Create a new mobile number
                if self.env['sms.number'].search_count([('mobile_number','=',av_phone)]) == 0:
                    vsms = self.env['sms.number'].create({'name': av_phone, 'mobile_number': av_phone,'account_id':self.id})
	        
	        payload = {'SmsUrl': str(request.httprequest.host_url + "sms/twilio/receive")}
	        requests.post("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/IncomingPhoneNumbers/" + sid, data=payload, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
                
        else:
            UserError("Bad Credentials")

