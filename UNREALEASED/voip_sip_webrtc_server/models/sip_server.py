# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json
import random
import openerp
import odoo
from random import randint
import time
import string
import socket
import re
import hashlib
from odoo import api, fields, models, registry
from odoo.exceptions import UserError, ValidationError
from openerp import SUPERUSER_ID, tools

class SIPServer(models.Model):

    _name = "sip.server"
    _description = "SIP Server"

    name = fields.Char(string="Name")
    port = fields.Integer(string="Port")
    sip_listen = True

    def sip_server_wrapper(self):
        #Set the environment before starting the main thread
        with api.Environment.manage():
            #As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self.sip_server()
            self._cr.close()
                    
    def sip_server(self):
        _logger.error("Start SIP Listening")
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', 5060));

        sip_tag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))

        while self.sip_listen:
            data, addr = serversocket.recvfrom(2048)
            
            if data == "DIE BOT DIE!!!":
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
            elif data.startswith("SIP/2.0 200 OK"):
                _logger.error("OK")
                self.verify_account(data)
                    
            elif data.startswith("SIP/2.0 401 Unauthorized"):
                _logger.error("Unauthorized")
                self.send_auth_register(data)

            elif data.startswith("ACK"):
                _logger.error("ack")
            elif data.startswith("INVITE"):
                _logger.error("invite")
                _logger.error(data)

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
                _logger.error(addr)
                serversocket.sendto(reply, addr)

                with api.Environment.manage():
                    # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
                    new_cr = self.pool.cursor()
                    self = self.with_env(self.env(cr=new_cr))
                    self.env['voip.voip'].start_incoming_sip_call(data, addr, sip_tag)
                    self._cr.close()
        
        #Close the socket
        _logger.error("SIP Shutdown")
        serversocket.shutdown(socket.SHUT_RDWR)
        serversocket.close()

    def start_sip_server(self):
        #Start a new thread so you don't block the main Odoo thread
        self.sip_socket_thread = threading.Thread(target=self.sip_server_wrapper, args=())
        self.sip_socket_thread.start()

    def stop_sip_server(self):
        _logger.error("Stop SIP Server")

        hostname = request.httprequest.host

        self.sip_listen = False
        
        #We need to send some data otherwise it gets stuck by 'serversocket.recvfrom(2048)', data is can be anything
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.sendto("DIE BOT DIE!!!", (hostname, 5060) )

    def verify_account(self, data):

            call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
            db_name = call_id.split("-")[0]
            type = call_id.split("-")[1]
            record_id = call_id.split("-")[2]

            #Connect to the saas database and update the subscription status
	    db = openerp.sql_db.db_connect(db_name)

            registry = odoo.modules.registry.Registry(db_name)
            with registry.cursor() as cr:
                
                context = {}
                env = api.Environment(cr, SUPERUSER_ID, context)
                voip_account = env['voip.account'].browse( int(record_id) )
                voip_account.verified = True

    def H(self, data):
        return hashlib.md5(data).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)
    
    def send_auth_register(self, data):
                
        _logger.error("Send Auth Register")

        try:

            call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
            db_name = call_id.split("-")[0]
            type = call_id.split("-")[1]
            record_id = call_id.split("-")[2]

            #Connect to the saas database and update the subscription status
	    db = openerp.sql_db.db_connect(db_name)

            registry = odoo.modules.registry.Registry(db_name)
            with registry.cursor() as cr:
                
                context = {}
                env = api.Environment(cr, SUPERUSER_ID, context)
                voip_account = env['voip.account'].browse( int(record_id) )
                
                authheader = re.findall(r'WWW-Authenticate: (.*?)\r\n', data)[0]
                        
                _logger.error(authheader)

                realm = re.findall(r'realm="(.*?)"', authheader)[0]
                method = "REGISTER"
                uri = "sip:" + voip_account.domain
                nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                qop = re.findall(r'qop="(.*?)"', authheader)[0]
                nc = "00000001"
                cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])

            
                #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                A1 = voip_account.auth_username + ":" + realm + ":" + voip_account.password
                A2 = method + ":" + uri
                response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )

                local_ip = env['ir.values'].get_default('voip.settings', 'server_ip')

                register_string = ""
                register_string += "REGISTER sip:" + voip_account.domain + " SIP/2.0\r\n"
                register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
                register_string += "Max-Forwards: 70\r\n"
                register_string += "Contact: <sip:" + voip_account.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
                register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + voip_account.address + ">\r\n"
                register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + voip_account.address + ">;tag=903df0a\r\n"
                register_string += "Call-ID: " + call_id + "\r\n"
                register_string += "CSeq: 2 REGISTER\r\n"
                register_string += "Expires: 3600\r\n"
                register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                register_string += 'Authorization: Digest username="' + voip_account.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + voip_account.domain + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                register_string += "Content-Length: 0\r\n"
                register_string += "\r\n"

                _logger.error("REGISTER: " + register_string)
        
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(register_string, (voip_account.outbound_proxy, 5060) )
            
        except Exception as e:
            _logger.error(e)        