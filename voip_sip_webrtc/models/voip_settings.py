# -*- coding: utf-8 -*-
import socket
import threading
import random
import string
import logging
import requests
_logger = logging.getLogger(__name__)
from openerp.http import request
import odoo
from openerp import api, fields, models

class VoipSettings(models.Model):

    _name = "voip.settings"

    missed_call_action = fields.Selection([('nothing', 'Nothing')], string="Missed Call Action", help="What action is taken when the call is missed")
    sip_listening = False

    def sip_server(self):
        _logger.error("Start SIP Listening")
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', 5060));

        sip_tag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))

        sip_listening = True
        while sip_listening:
            data, addr = serversocket.recvfrom(2048)

            if not data: 
                break
        
            _logger.error(data)

            #Read the body as a dictionary
            sip_dict = {}
            for line in data.split("\n"):
                sip_key = line.split(":")[0]
                sip_value = line[len(sip_key) + 2:]
                sip_dict[sip_key] = sip_value
        
            
            if data.startswith("OPTIONS"):
                _logger.error("options")
            elif data.startswith("REGISTER"):
                _logger.error("register")
            elif data.startswith("ACK"):
                _logger.error("ack")
            elif data.startswith("INVITE"):
                _logger.error("invite")


                #Send 180 Ringing
                reply = ""
                reply += "SIP/2.0 180 Ringing\r\n"
                reply += "Via: " + sip_dict['Via'].strip() + "\r\n"                
                reply += "From: " + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + sip_dict['To'].strip() + ";tag=" + str(sip_tag) + "\r\n"
                reply += "Contact: " + sip_dict['Contact'].strip() + "\r\n"
                reply += "Call-ID: " + sip_dict['Call-ID'].strip() + "\r\n"
                reply += "CSeq: " + sip_dict['CSeq'].strip() + "\r\n"
                reply += "Content-Length: 0\r\n"            
                #_logger.error("180 RINGING: " + reply )    
                serversocket.sendto(reply, addr)

                with api.Environment.manage():
                    # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
                    new_cr = self.pool.cursor()
                    self = self.with_env(self.env(cr=new_cr))
                    self.env['voip.voip'].start_incoming_sip_call(data, addr, sip_tag)
                    self._cr.close()
        
    def start_sip_server(self):
        #Start a new thread so you don't block the main Odoo thread
        sip_socket_thread = threading.Thread(target=self.sip_server, args=())
        sip_socket_thread.start()
        
    def stop_sip_server(self):
        _logger.error("Stop SIP Server")
        sip_listening = False