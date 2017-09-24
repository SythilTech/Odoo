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
                _logger.error("OPTIONS")
            elif data.startswith("REGISTER"):
                _logger.error("REGISTER")
            elif data.startswith("SIP/2.0 200 OK"):
                _logger.error("OK")

                call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
                type = call_id.split("-")[1]

                if type == "account":                
                    self.verify_account(data)
                elif type == "call":
                    self.pass_sdp(data)
                    
            elif data.startswith("SIP/2.0 401 Unauthorized"):
                _logger.error("Unauthorized")
                self.send_auth_register(data)
            elif data.startswith("ACK"):
                _logger.error("ack")
            elif data.startswith("SIP/2.0 407 Proxy Authentication Required"):
                _logger.error("407")
                self.send_auth_invite(data)
            elif data.startswith("INVITE"):
                _logger.error("invite")
        
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

    def pass_sdp(self, data):

        _logger.error("Call OK get SDP")

        call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]    
        content_length = re.findall(r'Content-Length: (.*?)\r\n', data)[0]
        
        #SDP should always be split by a blank link, if there are multiple blank lines the SIP 200 OK is malformed anyway
        sdp = data.split("\r\n\r\n")[1]
        _logger.error(sdp)
        
        db_name = call_id.split("-")[0]
        type = call_id.split("-")[1]
        record_id = call_id.split("-")[2]

    def verify_account(self, data):

            _logger.error("OK Account Verified")

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
                
                if self.env['sip.account'].search_count([('address','=', voip_account.address)]) == 0:
                    self.env['sip.account'].create({'database': db_name, 'address': voip_account.address, 'password': voip_account.password, 'auth_username': voip_account.auth_usernam, 'username': voip_account.username, 'domain': voip_account.domain, 'outbound_proxy': voip_account.outbound_proxy})

    def H(self, data):
        return hashlib.md5(data).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)

    def send_auth_invite(self, data):
                
        _logger.error("Send Auth INVITE")

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
                voip_call = env['voip.call'].browse( int(record_id) )                
                voip_account = voip_call.voip_account

                local_ip = env['ir.values'].get_default('voip.settings', 'server_ip')


                #reply = ""
                #reply += "ACK sip:" + voip_call.partner_id.sip_address + " SIP/2.0\r\n"
                #reply += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
                #reply += "Max-Forwards: 70\r\n"
                #reply += 'To: <sip:' + voip_call.partner_id.sip_address.strip() + ">\r\n"
                #reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + voip_account.address + ">;tag=903df0a\r\n"
                #reply += "Call-ID: " + call_id + "\r\n"
                #reply += "CSeq: 1 ACK\r\n"
                #reply += "Content-Length: 0\r\n"

                #serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                #serversocket.sendto(reply, (voip_account.outbound_proxy, 5060) )

                #_logger.error("ACK: " + reply)
                
                authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                        
                realm = re.findall(r'realm="(.*?)"', authheader)[0]
                method = "INVITE"
                uri = "sip:" + voip_call.partner_id.sip_address
                nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                qop = re.findall(r'qop="(.*?)"', authheader)[0]
                nc = "00000001"
                cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])

                #Sample Data (response works)
                #realm = "jnctn.net"
                #method = "INVITE"
                #uri = "sip:stevewright2009@sythiltech.onsip.com"
                #nonce = "59c04f390000acd39cf6455cc0c0a799d5466278a0b637ca"
                #qop = "auth"
                #nc = "00000001"
                #cnonce = "be52ae979f0ee91add06f637dbf41f0d"
            
                #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                A1 = voip_account.auth_username + ":" + realm + ":" + voip_account.password
                A2 = method + ":" + uri
                response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )
                
                reply = ""
                reply += "INVITE sip:" + voip_call.partner_id.sip_address.strip() + " SIP/2.0\r\n"
                reply += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
                reply += "Max-Forwards: 70\r\n"
                reply += "Contact: <sip:" + voip_account.username + "@" + local_ip + ":5060>\r\n"
                reply += 'To: "' + voip_call.partner_id.name + '"<sip:' + voip_call.partner_id.sip_address.strip() + ">\r\n"
                reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + voip_account.address + ">;tag=903df0a\r\n"
                reply += "Call-ID: " + call_id + "\r\n"
                reply += "CSeq: 2 INVITE\r\n"
                reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += 'Proxy-Authorization: Digest username="' + voip_account.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + voip_call.partner_id.sip_address + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                reply += "Supported: replaces\r\n"
                reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                #reply += "Content-Length: " + str(len(voip_call.from_partner_sdp)) + "\r\n"
                #reply += "\r\n"
                #Dislikes SDP data?!?
                #reply += voip_call.from_partner_sdp

                #Sample data webrtc
                #v=0\r\n
                #o=mozilla...THIS_IS_SDPARTA-55.0.3 8294658421909368638 0 IN IP4 0.0.0.0\r\n
                #s=-\r\n
                #t=0 0\r\n
                #a=fingerprint:sha-256 ED:FF:6A:68:8E:67:47:0E:A8:F7:D9:92:5F:20:4D:D4:B2:1A:3B:97:7D:B9:AA:02:0C:7F:0E:5A:64:FA:6E:A2\r\n
                #a=group:BUNDLE sdparta_0\r\n
                #a=ice-options:trickle\r\n
                #a=msid-semantic:WMS *\r\n
                #m=audio 9 UDP/TLS/RTP/SAVPF 109 9 0 8 101\r\n
                #c=IN IP4 0.0.0.0\r\n
                #a=sendrecv\r\n
                #a=extmap:1/sendonly urn:ietf:params:rtp-hdrext:ssrc-audio-level\r\n
                #a=fmtp:109 maxplaybackrate=48000;stereo=1;useinbandfec=1\r\n
                #a=fmtp:101 0-15\r\n
                #a=ice-pwd:3289a8fe04b88eeb11eae873568c7fe8\r\n
                #a=ice-ufrag:0a38dbfd\r\n
                #a=mid:sdparta_0\r\n
                #a=msid:{6ac1d3e6-0c31-4985-b007-58d09e6cdd6a} {4dd601cd-9f91-408f-8095-16386a5e5458}\r\n
                #a=rtcp-mux\r\n
                #a=rtpmap:109 opus/48000/2\r\n
                #a=rtpmap:9 G722/8000/1\r\n
                #a=rtpmap:0 PCMU/8000\r\n
                #a=rtpmap:8 PCMA/8000\r\n
                #a=rtpmap:101 telephone-event/8000/1\r\n
                #a=setup:actpass\r\n
                #a=ssrc:2976186053 cname:{d6f01826-125a-4974-a8b1-0439bdd082a3}\r\n


                #Sample data X-Lite
                sdp = ""
                sdp += "v=0\r\n"
                sdp += "o=- 13150342053296106 1 IN IP4 192.168.1.133\r\n"
                sdp += "s=X-Lite release 5.0.1 stamp 86895\r\n"
                sdp += "c=IN IP4 192.168.1.133\r\n"
                sdp += "t=0 0\r\n"
                sdp += "m=audio 53194 RTP/AVP 9 8 85 120 0 84 3 101\r\n"
                sdp += "a=rtpmap:85 speex/8000\r\n"
                sdp += "a=rtpmap:120 opus/48000/2\r\n"
                sdp += "a=fmtp:120 useinbandfec=1; usedtx=1; maxaveragebitrate=64000\r\n"
                sdp += "a=rtpmap:84 speex/16000\r\n"
                sdp += "a=rtpmap:101 telephone-event/8000\r\n"
                sdp += "a=fmtp:101 0-15\r\n"
                sdp += "a=sendrecv\r\n"

                #Should be 365
                reply += "Content-Length: " + str(len(sdp)) + "\r\n"
                reply += "\r\n"
                reply += sdp
                
        
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(reply, (voip_account.outbound_proxy, 5060) )

                _logger.error("INVITE AUTH: " + reply)
                _logger.error("END INVITE AUTH")
                
        except Exception as e:
            _logger.error(e)
            
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