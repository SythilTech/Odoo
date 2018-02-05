# -*- coding: utf-8 -*-
import requests
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
import urllib

from openerp.http import request
from openerp import api, fields, models
from openerp.exceptions import UserError

class sms_response():
     delivary_state = ""
     response_string = ""
     human_read_error = ""
     mms_url = ""
     message_id = ""

class SmsGatewayTwilio(models.Model):

    _name = "sms.gateway.yeastar"
    _description = "Yeastar SMS Gateway"
    
    api_url = fields.Char(string="API URL")
    
    def send_message(self, sms_gateway_id, from_number, to_number, sms_content, my_model_name='', my_record_id=0, media=None, queued_sms_message=None):
        """Actual Sending of the sms"""
        sms_account = self.env['sms.account'].search([('id','=',sms_gateway_id)])
        
        #format the from number before sending
        format_from = from_number
        format_from = format_from.replace(" ", "").replace("+","")
        
        #format the to number before sending
        format_to = to_number
        format_to = format_to.replace(" ", "").replace(u'\xa0', "").replace("+","00")
        
        url = sms_account.yeastar_url + "=account=" + sms_account.yeastar_username + "&password=" + sms_account.yeastart_password + "&port=" + str(sms_account.yeastar_port) + "&destination=" + urllib.quote(format_to) + "&content=" + urllib.quote(sms_content)
        _logger.error(url)
        response_string = requests.get(url)
        
        _logger.error(response_string.text)

        delivary_state = "successful"
        human_read_error = ""
        sms_gateway_message_id = "?"
        
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
                
class SmsAccountYeastar(models.Model):

    _inherit = "sms.account"
    _description = "Adds the yeastar specfic gateway settings to the sms gateway accounts"
    
    yeastar_url = fields.Char(string="Yeastar URL", default="http://localhost/cgi/WebCGI?1500101")
    yeastar_port = fields.Integer(string="Port")
    yeastar_username = fields.Char(string="Username")
    yeastart_password = fields.Char(string="Password")