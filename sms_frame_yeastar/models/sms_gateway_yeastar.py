# -*- coding: utf-8 -*-
import requests
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
import urllib
import socket
import telnetlib
import threading
from openerp.exceptions import UserError
import re
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

class SmsGatewayYeastar(models.Model):

    _name = "sms.gateway.yeastar"
    _description = "Yeastar SMS Gateway"
    
    api_url = fields.Char(string="API URL")
    
    def send_message(self, sms_gateway_id, from_number, to_number, sms_content, my_model_name='', my_record_id=0, media=None, queued_sms_message=None, media_filename=False):
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
    yeastar_port = fields.Integer(string="GSM Port")
    yeastar_username = fields.Char(string="Username")
    yeastart_password = fields.Char(string="Password")
    yeastar_host = fields.Char(string="Host")
    yeastar_api_port = fields.Integer(string="API Port", default="5038")
    
    def yeastar_connect(self):
        _logger.error("Yeastar Connect")
                
        #Don't block the main thread with all the listening
        yeastar_listener_starter = threading.Thread(target=self.yeastar_connect_thread, args=())
        yeastar_listener_starter.start()

    def yeastar_connect_thread(self):
        _logger.error("Yeastar Connect Thread")

        try:
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))

                tn = telnetlib.Telnet(self.yeastar_host, self.yeastar_api_port)

                tn.write("Action: Login\r\nUsername: " + self.yeastar_username.encode("utf-8") + "\r\nSecret: " + self.yeastart_password.encode("utf-8") + "\r\n\r\n")
        
                login_response = tn.read_until("\r\n\r\n")
                if "Success" not in login_response:
                    raise UserError("Login Failed")        
        
                stage = "WAIT"
                while stage == "WAIT":
                    sms_event_data = tn.read_until("\r\n\r\n")
                    #sms_event_data = "Event: ReceivedSMS\r\nID: 768\r\nSender: +61437950593\r\nSmsc: +555\r\nRecvtime: 2013-11-27 09:39:46\r\nContent: Hello From Yeastar\r\n\r\n"
                    _logger.error(sms_event_data)
                    sms_event = re.findall(r'Event: (.*?)\r\n', sms_event_data)[0]
                    if sms_event == "ReceivedSMS":
                        sms_id = re.findall(r'ID: (.*?)\r\n', sms_event_data)[0]
                        sms_sender = re.findall(r'Sender: (.*?)\r\n', sms_event_data)[0]
                        sms_to = "?"
                        sms_receive_time = re.findall(r'Recvtime: (.*?)\r\n', sms_event_data)[0]
                        sms_content = re.findall(r'Content: (.*?)\r\n', sms_event_data)[0]
                        sms_content = sms_content.replace("+"," ")
                        sms_content = urllib.unquote(sms_content)
            
                        _logger.error(sms_sender)
                        
                        create_dict = {'account_id': self.id, 'status_code': "RECEIVED", 'from_mobile': sms_sender, 'to_mobile': sms_to, 'sms_gateway_message_id': sms_id, 'sms_content': sms_content, 'direction':'I', 'message_date': sms_receive_time}

                        sender_partner = self.env['res.partner'].search([('mobile_without_spaces','=',sms_sender)])
                        if sender_partner:
                            model_id = self.env['ir.model'].search([('model','=', 'res.partner')])
                            create_dict['model_id'] = model_id.id
                            create_dict['record_id'] = int(sender_partner.id)
                            create_dict['by_partner_id'] = sender_partner.id
            
                            discussion_subtype = self.env['ir.model.data'].get_object('mail', 'mt_comment')
            
                            my_message = sender_partner.message_post(body=sms_content, subject="SMS Received", subtype_id=discussion_subtype.id, author_id=sender_partner.id, message_type="comment")

                            #Notify followers of this partner who are listenings to the 'discussions' subtype
                            for notify_partner in self.env['mail.followers'].search([('res_model','=','res.partner'),('res_id','=',sender_partner.id), ('subtype_ids','=',discussion_subtype.id)]):
                                my_message.needaction_partner_ids = [(4,notify_partner.partner_id.id)]

                        
                        #Create the sms record in history
                        history_id = self.env['sms.message'].create(create_dict)

                        #Have to manually commit the new cursor now since we are in a loop
                        self.env.cr.commit()                        

                self._cr.close()

        except Exception as e:
            _logger.error(e)
