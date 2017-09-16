# -*- coding: utf-8 -*-
import socket
import logging
from openerp.exceptions import UserError
_logger = logging.getLogger(__name__)
from openerp.http import request
import re
import digestauth
import hashlib
import random
from openerp import api, fields, models

class VoipAccount(models.Model):

    _name = "voip.account"
    _rec_name = "address"

    address = fields.Char(string="SIP Address")
    password = fields.Char(string="SIP Password")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username")
    domain = fields.Char(string="Domain")
    outbound_proxy = fields.Char(string="Outbound Proxy")
    verified = fields.Boolean(string="Verified")
    
    @api.onchange('address')
    def _onchange_address(self):
        if self.address:
            if "@" in self.address:
                self.username = self.address.split("@")[0]
                self.domain = self.address.split("@")[1]
        
    def send_register(self):
    
        self.env['voip.settings'].stop_sip_server()

        #Turn on the SIP server if it is not already started    
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if sock.connect_ex(('',5060)) == 0:
            self.env['voip.settings'].start_sip_server()

        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        register_string = ""
        register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
        register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">\r\n"
        register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        register_string += "Call-ID: " + "account" + str(self.id) + "\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        register_string += "Expires: 3600\r\n"
        register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"

        _logger.error("REGISTER: " + register_string)
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.sendto(register_string, (self.outbound_proxy, 5060) )

    def H(self, data):
        return hashlib.md5(data).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)

    def verify_account(self, data):
        self.verified = True
    
    def send_auth_register(self, data):
                
        _logger.error("Send Auth Register 10")

        try:

            #Otherwise the thread won't die and we can't test new code        
            self.env['voip.settings'].stop_sip_server()
        
            authheader = re.findall(r'WWW-Authenticate: (.*?)\r\n', data)[0]
                        
            _logger.error(authheader)

            realm = re.findall(r'realm="(.*?)"', authheader)[0]
            method = "REGISTER"
            uri = "sip:" + self.domain
            nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
            qop = re.findall(r'qop="(.*?)"', authheader)[0]
            nc = "00000001"
            cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])

            #Test Data
            #realm = "jnctn.net"
            #method = "REGISTER"
            #uri = "sip:sythiltech.onsip.com"
            #nonce = "59bbb7cb0000a9be68baba61af12783b405f54a5e1608403"           
            #qop = "auth"
            #nc = "00000001"
            #cnonce = "5def9347d2582bb561e3f09aa9940678"
            
            #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
            #request-digest  = <"> < KD ( H(A1), unq(nonce-value)
            #                              ":" nc-value
            #                              ":" unq(cnonce-value)
            #                              ":" unq(qop-value)
            #                              ":" H(A2)
            #                      ) <">
            A1 = self.auth_username + ":" + realm + ":" + self.password
            A2 = method + ":" + uri
            response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )
            _logger.error(response)

            local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

            register_string = ""
            register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
            register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
            register_string += "Max-Forwards: 70\r\n"
            register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
            register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">\r\n"
            register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
            register_string += "Call-ID: " + "account" + str(self.id) + "\r\n"
            register_string += "CSeq: 2 REGISTER\r\n"
            register_string += "Expires: 3600\r\n"
            register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
            register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
            register_string += 'Authorization: Digest username="' + self.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + self.domain + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
            register_string += "Content-Length: 0\r\n"
            register_string += "\r\n"

            _logger.error("REGISTER: " + register_string)
        
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            serversocket.sendto(register_string, (self.outbound_proxy, 5060) )
            
        except Exception as e:
            _logger.error(e)
            self.env['voip.settings'].stop_sip_server()        
