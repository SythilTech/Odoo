# -*- coding: utf-8 -*-
import socket
import logging
_logger = logging.getLogger(__name__)
from openerp.http import request
import re

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
    
    @api.onchange('address')
    def _onchange_address(self):
        if self.address:
            if "@" in self.address:
                self.username = self.address.split("@")[0]
                self.domain = self.address.split("@")[1]
        
    def send_register(self):

        #Turn on the SIP server if it is not already started    
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if sock.connect_ex(('',5060)) == 0:
            self.env['voip.settings'].start_sip_server()


        #local_ip = request.httprequest.headers.environ['HTTP_HOST'].split(":")[0]
        local_ip = "13.54.58.172"


    #Request-Line: REGISTER sip:sythiltech.onsip.com SIP/2.0
    #    Method: REGISTER
    #    Request-URI: sip:sythiltech.onsip.com
    #    [Resent Packet: False]
    #Message Header
    #    Via: SIP/2.0/UDP 10.0.0.68:54443;branch=z9hG4bK-524287-1---9ee90b2fd7b87612;rport
    #    Max-Forwards: 70
    #    Contact: <sip:steven@10.0.0.68:54443;rinstance=515ca81874fc59c3>
    #    To: "Steven"<sip:steven@sythiltech.onsip.com>
    #    From: "Steven"<sip:steven@sythiltech.onsip.com>;tag=119e0608
    #    Call-ID: 86895Zjg1YjA0MGFmYTQ5MDBlYzQ4NGE1YjE3NGIzNTk4YTE
    #    CSeq: 1 REGISTER
    #    Expires: 3600
    #    Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE
    #    User-Agent: X-Lite release 5.0.1 stamp 86895
    #    Content-Length: 0


        register_string = ""
        register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
        register_string += 'To: "' + request.env.user_id.partner_id.name + '"<sip:' + self.address + ">\r\n"
        register_string += 'From: "' + request.env.user_id.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        register_string += "Call-ID: " + "account" + str(self.id) + "\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        register_string += "Expires: 3600\r\n"
        register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"
        
        proxy_ip = self.outbound_proxy
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.sendto(register_string, (proxy_ip, 5060) )

        _logger.error("REGISTER: " + register_string)

    def send_auth_register(self, data):
                

        
        register_string = ""
        register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
        register_string += 'To: "' + request.env.user_id.partner_id.name + '"<sip:' + self.address + ">\r\n"
        register_string += 'From: "' + request.env.user_id.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        register_string += "Call-ID: " + "account" + str(self.id) + "\r\n"
        register_string += "CSeq: 2 REGISTER\r\n"
        register_string += "Expires: 3600\r\n"
        register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"

        #WWW-Authenticate: Digest realm="jnctn.net", nonce="59a4d3ee00016d46657413fef0d47eb5d9d946272285b4cc", qop="auth"        
        #Authentication Scheme: Digest
        #Realm: "jnctn.net"
        #Nonce Value: "59a4d3ee00016d46657413fef0d47eb5d9d946272285b4cc"
        #QOP: "auth"
        
        register_string += 'Authorization: Digest username="' + auth_username + '",realm="jnctn.net",nonce="59a4d3ee00016d46657413fef0d47eb5d9d946272285b4cc",uri="sip:' + self.domain + '",response="28a1e11d9deb081dbec67b272f7f295b",cnonce="86071da701177f777b5f10025",nc=00000001,qop:auth,algorithm=MD5'



        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"