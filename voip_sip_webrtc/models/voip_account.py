# -*- coding: utf-8 -*-
import socket
import logging
from openerp.exceptions import UserError
_logger = logging.getLogger(__name__)
#l = logging.getLogger("pydub.converter")
#l.setLevel(logging.DEBUG)
#l.addHandler(logging.StreamHandler())
from openerp.http import request
import re
import hashlib
import random
from openerp import api, fields, models
import threading
import time
import struct
import base64
from random import randint
            
class VoipAccount(models.Model):

    _name = "voip.account"
    _rec_name = "address"

    type = fields.Selection([('sip', 'SIP'), ('xmpp', 'XMPP')], default="sip", string="Account type")
    address = fields.Char(string="SIP Address")
    password = fields.Char(string="SIP Password")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username")
    domain = fields.Char(string="Domain")
    outbound_proxy = fields.Char(string="Outbound Proxy")
    verified = fields.Boolean(string="Verified")
    wss = fields.Char(string="WSS", default="wss://edge.sip.onsip.com")
    gsm_media = fields.Binary(string="(OBSOLETE)GSM Audio File")
    media = fields.Binary(string="Raw Audio File")
    codec_id = fields.Many2one('voip.codec', string="Codec")
    
    @api.onchange('address')
    def _onchange_address(self):
        if self.address:
            if "@" in self.address:
                self.username = self.address.split("@")[0]
                self.domain = self.address.split("@")[1]
            
    def H(self, data):
        return hashlib.md5(data).hexdigest()

    def KD(self, secret, data):
        return self.H(secret + ":" + data)
    
    def generate_rtp_packet(self, audio_stream, codec, sequence_number):

        rtp_data = ""

        #---- Compose RTP packet to send back---
        #10.. .... = Version: RFC 1889 Version (2)
        #..0. .... = Padding: False
        #...0 .... = Extension: False
        #.... 0000 = Contributing source identifiers count: 0
        rtp_data += "80"

        #0... .... = Marker: False
        #Payload type: G.711 aLaw or GSM
        rtp_data += " " + format( codec.payload_type, '02x')

        rtp_data += " " + format( sequence_number, '04x')
        
        timestamp = codec.sample_rate / (1000 / codec.sample_interval) * sequence_number
        rtp_data += " " + format( timestamp, '08x')
            
        #Synchronization Source identifier: 0x1222763d (304248381)
        rtp_data += " 12 22 76 3d"

        #Payload:
        payload_data = audio_stream[sequence_number * codec.payload_size : sequence_number * codec.payload_size + codec.payload_size]
        hex_string = ""

        for rtp_char in payload_data:
            hex_format = "{0:02x}".format(ord(rtp_char))
            hex_string += hex_format + " "

        rtp_data += " " + hex_string
            
        return rtp_data.replace(" ","").decode('hex')
            
    def rtp_server_listener(self, media_port, audio_stream, codec, model=False, record_id=False):
        
        try:

            _logger.error("Start RTP Listening on Port " + str(media_port) )
                
            rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtpsocket.bind(('', media_port));

            stage = "LISTEN"
            hex_string = ""
            joined_payload = ""
            packet_count = 0

            #Send audio data out every 20ms
            #sequence_number = randint(29161, 30000)
            sequence_number = 0
            
            while stage == "LISTEN":

                rtpsocket.settimeout(10)
                data, addr = rtpsocket.recvfrom(2048)
                
                if packet_count % 10 == 0:
                    _logger.error(data)
                    
                joined_payload += data
                packet_count += 1

                #---------------------Send Audio Packet-----------
                send_data = self.generate_rtp_packet(audio_stream, codec, sequence_number)
                rtpsocket.sendto(send_data, addr)
                sequence_number += 1
                #---------------------END Send Audio Packet-----------

        except Exception as e:
            _logger.error(e)

        try:

            #Create the call with the audio
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))

                #Start off with the raw audio stream
                create_dict = {'media': joined_payload, 'media_filename': "call.raw", 'codec_id': codec.id}
                self.process_audio_stream( create_dict )

                if model:
                    #Add to the chatter
                    #TODO add SIP subtype
                    self.env[model].browse( int(record_id) ).message_post(body="Call Made", subject="Call Made", message_type="comment")

                #Have to manually commit the new cursor?
                self.env.cr.commit()
        
                self._cr.close()


        except Exception as e:
            _logger.error(e)

    def test_add_header(self):
        #G.711
        with open("/odoo/call.raw", "rb") as audio_file:
            audio_stream = audio_file.read()
	    #header = "52 49 46 46 54 48 18 00 57 41 56 45 66 6D 74 20 12 00 00 00 06 00 01 00 40 1F 00 00 40 1F 00 00 01 00 08 00 00 00 66 61 63 74 04 00 00 00 00 48 18 00 4C 49 53 54 1A 00 00 00 49 4E 46 4F 49 53 46 54 0E 00 00 00 4C 61 76 66 35 35 2E 33 33 2E 31 30 30 00 64 61 74 61 00 48 18 00"

            header = ""
	    #"RIFF"
	    header += "52 49 46 46"
	    
	    #File Size (Integer)?
	    header += " " + format(len(audio_stream) - 8, '08x')
	    
	    #"WAVE"
	    header += " 57 41 56 45"
	    
	    #"fmt "
	    header += " 66 6D 74 20"
	    
	    #Format data length (18)?
	    header + "12 00 00 00"
	    
	    #Type of format (6)?
	    header += " 06 00"
	    
	    #Channels (mono)
	    header += " 01 00"
	    
	    #Sample rate (1 milion???)
	    header += " 40 1F 00 00 40"
	    
	    #c?
	    header += " 1F 00 00 01"
	    
	    #c2?
	    header += " 00 08 00 00"
	    
	    #Bits per sample (102?)
	    header += " 00 66"
	    
	    #no idea...
	    header += " 61 63 74 04 00 00 00 00 48 18 00 4C 49 53 54 1A 00 00 00 49 4E 46 4F 49 53 46 54 0E 00 00 00 4C 61 76 66 35 35 2E 33 33 2E 31 30 30 00"
            
            #"data"
            header += " 64 61 74 61"
            
            #Data length
            header += " " + format( (len(audio_stream) - 44) / 3 , '08x')


	    header = "52 49 46 46"	    
	    header += " " + struct.pack('<I', len(audio_stream) - 8 ).encode('hex')
	    header += " 57 41 56 45 66 6D 74 20 12 00 00 00 06 00 01 00 40 1F 00 00 40 1F 00 00 01 00 08 00 00 00 66 61 63 74 04 00 00 00 00 48 18 00 4C 49 53 54 1A 00 00 00 49 4E 46 4F 49 53 46 54 0E 00 00 00 4C 61 76 66 35 35 2E 33 33 2E 31 30 30 00 64 61 74 61"
	    header += " " + struct.pack('<I', len(audio_stream) - 44 ).encode('hex')
            
            joined_payload_with_header = header.replace(" ","").decode('hex') + audio_stream

        with open("/odoo/call.wav", "wb") as audio_file:            
            audio_file.write(joined_payload_with_header)
    
    def test_make_call(self):

        with open("/odoo/input.raw", "rb") as audio_file:
            audio_stream = audio_file.read()
            codec = self.env['voip.codec'].browse(1)
            self.make_call("stevewright2009@sythiltech.onsip.com", audio_stream, codec)
            
    def make_call(self, to_address, audio_stream, codec, model=False, record_id=False):

        port = random.randint(6000,7000)
        media_port = random.randint(55000,56000)
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')
        call_id = random.randint(50000,60000)
        from_tag = random.randint(8000000,9000000)

        rtc_listener_starter = threading.Thread(target=self.rtp_server_listener, args=(media_port, audio_stream, codec, model, record_id,))
        rtc_listener_starter.start()
        
        #----Generate SDP of audio call that the server can work with e.g. limited codex support----
        sdp = ""
        
        #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
        sdp += "v=0\r\n"

        #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2 (Should come up with a better session id...)
        sess_id = int(time.time()) #Not perfect but I don't expect more then one call a second
        sess_version = 0 #Will always start at 0
        sdp += "o=- " + str(sess_id) + " " + str(sess_version) + " IN IP4 " + local_ip + "\r\n"
        
        #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3 (We don't need a session name, information about the call is all displayed in the UI)
        sdp += "s= \r\n"
        
        #Connection Information
        sdp += "c=IN IP4 " + local_ip + "\r\n"

        #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9 (For now sessions are infinite but we may use this if for example a company charges a price for a fixed 30 minute consultation)        
        sdp += "t=0 0\r\n"

        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        sdp += "m=audio " + str(media_port) + " RTP/AVP " + str(codec.payload_type) + "\r\n"

        #Two way call because later we may use voice reconisation to control assistant menus        
        sdp += "a=sendrecv\r\n"

        invite_string = ""
        invite_string += "INVITE sip:" + to_address + " SIP/2.0\r\n"
        invite_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
        invite_string += "Max-Forwards: 70\r\n"
        invite_string += "Contact: <sip:" + self.username + "@" + local_ip + ":" + str(port) + ">\r\n"
        invite_string += 'To: <sip:' + to_address + ">\r\n"
        invite_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=" + str(from_tag) + "\r\n"
        invite_string += "Call-ID: " + self.env.cr.dbname + "-call-" + str(call_id) + "\r\n"
        invite_string += "CSeq: 1 INVITE\r\n"
        invite_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        invite_string += "Content-Type: application/sdp\r\n"
        invite_string += "Supported: replaces\r\n"
        invite_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        invite_string += "Content-Length: " + str(len(sdp)) + "\r\n"
        invite_string += "\r\n"
        invite_string += sdp
         
        sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sipsocket.bind(('', port));

        sipsocket.sendto(invite_string, (self.outbound_proxy, 5060) )
        
        #Wait and send back the auth reply
        stage = "WAITING"
        while stage == "WAITING":

            data, addr = sipsocket.recvfrom(2048)
 
            #Send auth response if challenged
            if data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication Required":
                
                authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                         
                realm = re.findall(r'realm="(.*?)"', authheader)[0]
                method = "INVITE"
                uri = "sip:" + to_address
                nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                qop = re.findall(r'qop="(.*?)"', authheader)[0]
                nc = "00000001"
                cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])
 
                #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                A1 = self.auth_username + ":" + realm + ":" + self.password
                A2 = method + ":" + uri
                response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )

                reply = ""
                reply += "INVITE sip:" + to_address + " SIP/2.0\r\n"
                reply += "Via: SIP/2.0/UDP " + local_ip + ":" + str(port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
                reply += "Max-Forwards: 70\r\n"
                reply += "Contact: <sip:" + self.username + "@" + local_ip + ":" + str(port) + ">\r\n"
                reply += 'To: <sip:' + to_address + ">\r\n"
                reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=" + str(from_tag) + "\r\n"
                reply += "Call-ID: " + self.env.cr.dbname + "-call-" + str(call_id) + "\r\n"
                reply += "CSeq: 2 INVITE\r\n"
                reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += 'Proxy-Authorization: Digest username="' + self.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + to_address + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                reply += "Supported: replaces\r\n"
                reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                reply += "Content-Length: " + str(len(sdp)) + "\r\n"
                reply += "\r\n"
                reply += sdp        
             
                sipsocket.sendto(reply, addr)
            elif data.split("\r\n")[0] == "SIP/2.0 404 Not Found":
                stage = "Not Found"
                return False
            elif data.split("\r\n")[0] == "SIP/2.0 403 Forbidden":
                #Likely means call was rejected
                stage = "Forbidden"
                return False
            elif data.startswith("BYE"):
                #Do stuff when the call is ended by client
                stage = "BYE"
                return True
            elif data.split("\r\n")[0] == "SIP/2.0 200 OK":

                contact_header = re.findall(r'Contact: <(.*?)>\r\n', data)[0]
                rtp_ip = re.findall(r'\*(.*?)!', contact_header)[0]
                record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                send_media_port = int(re.findall(r'm=audio (.*?) RTP', data)[0])
        
                #Send the ACK
                reply = ""
                reply += "ACK " + contact_header + " SIP/2.0\r\n"
                reply += "Via: SIP/2.0/UDP " + local_ip + ":" + str(port) + ";branch=z9hG4bK-524287-1---41291a6583a6634f;rport\r\n"
                reply += "Max-Forwards: 70\r\n"
                reply += "Route: " + record_route + "\r\n"
                reply += "Contact: <sip:" + self.username + "@" + local_ip + ":" + str(port) + ">\r\n"
                reply += 'To: <sip:' + to_address + ">;tag=fa68ca4e\r\n"
                reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
                reply += "Call-ID: " + self.env.cr.dbname + "-call-" + str(call_id) + "\r\n"
                reply += "CSeq: 1 ACK\r\n"
                reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                reply += "Content-Length: 0\r\n"
                reply += "\r\n"

                sipsocket.sendto(reply, addr)
                
                stage = "SENT"

                return True
 
    def send_message(self, to_address, message_body, model=False, record_id=False):
  
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        port = 8071

        message_string = ""
        message_string += "MESSAGE sip:" + self.domain + " SIP/2.0\r\n"
        message_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(port) + "\r\n"
        message_string += "Max-Forwards: 70\r\n"
        message_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + to_address + ">;messagetype=IM\r\n"
        message_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        message_string += "Call-ID: 86895YTZlZGM3MzFkZTk4MzA2NGE0NjU3ZGExNmU5NTE1ZDM\r\n"
        message_string += "CSeq: 1 MESSAGE\r\n"
        message_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        message_string += "Content-Type: text/html\r\n"
        message_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        message_string += "Content-Length: " + str(len(message_body)) + "\r\n"
        message_string += "\r\n"
        message_string += message_body
        
        sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sipsocket.bind(('', port));

        sipsocket.sendto(message_string, (self.outbound_proxy, 5060) )
        
        #Wait and send back the auth reply
        stage = "WAITING"
        while stage == "WAITING":
            sipsocket.settimeout(10)        
            data, addr = sipsocket.recvfrom(2048)

            #Send auth response if challenged
            if data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication Required":
            
                authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                        
                realm = re.findall(r'realm="(.*?)"', authheader)[0]
                method = "MESSAGE"
                uri = "sip:" + to_address
                nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                qop = re.findall(r'qop="(.*?)"', authheader)[0]
                nc = "00000001"
                cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])

                #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                A1 = self.auth_username + ":" + realm + ":" + self.password
                A2 = method + ":" + uri
                response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )

                reply = ""
                reply += "MESSAGE sip:" + self.domain + " SIP/2.0\r\n"
                reply += "Via: SIP/2.0/UDP " + local_ip + ":" + str(port) + "\r\n"
                reply += "Max-Forwards: 70\r\n"
                reply += 'To: "' + self.env.user.partner_id.name + '"<sip:' + to_address + ">;messagetype=IM\r\n"
                reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
                reply += "Call-ID: 86895YTZlZGM3MzFkZTk4MzA2NGE0NjU3ZGExNmU5NTE1ZDM\r\n"
                reply += "CSeq: 2 MESSAGE\r\n"
                reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                reply += "Content-Type: text/html\r\n"
                reply += 'Proxy-Authorization: Digest username="' + self.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + to_address + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                reply += "Content-Length: " + str(len(message_body)) + "\r\n"
                reply += "\r\n"
                reply += message_body
            
                sipsocket.sendto(reply, addr)
            elif data.split("\r\n")[0] == "SIP/2.0 404 Not Found":
                stage = "FAILURE"
                return False
            elif data.split("\r\n")[0] == "SIP/2.0 200 OK":
                stage = "SENT"
                
                if model:
                    #Add to the chatter
                    #TODO add SIP subtype
                    self.env[model].browse( int(record_id) ).message_post(body=message_body, subject="SIP Message Sent", message_type="comment")

                return True

    def rtp_server_sender(self, media_port, audio_stream, caller_addr, model=False, record_id=False):
        
        try:

            _logger.error("Start RTP Listening on Port " + str(media_port) )
                
            rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtpsocket.bind(('', media_port));

            stage = "LISTEN"
            hex_string = ""
            joined_payload = ""
            packet_count = 0

            #Send audio data out every 20ms
            #sequence_number = randint(29161, 30000)
            sequence_number = 0
            
            while stage == "LISTEN":

                #---------------------Send Audio Packet-----------
                send_data = self.generate_rtp_packet(audio_stream, self.codec_id, sequence_number)
                rtpsocket.sendto(send_data, caller_addr)
                sequence_number += 1
                #---------------------END Send Audio Packet-----------

                rtpsocket.settimeout(10)
                data, addr = rtpsocket.recvfrom(2048)

                if packet_count % 10 == 0:
                    _logger.error(data)
                    
                joined_payload += data
                packet_count += 1

        except Exception as e:
            _logger.error(e)

        try:

            #Create the call with the audio
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))

                #Start off with the raw audio stream
                create_dict = {'media': joined_payload, 'media_filename': "call.raw", 'codec_id': self.codec_id.id}
                self.process_audio_stream( create_dict )

                if model:
                    #Add to the chatter
                    #TODO add SIP subtype
                    self.env[model].browse( int(record_id) ).message_post(body="Call Made", subject="Call Made", message_type="comment")

                #Have to manually commit the new cursor?
                self.env.cr.commit()
        
                self._cr.close()


        except Exception as e:
            _logger.error(e)

    def process_audio_stream(self, create_dict):
        _logger.error("Process File")
        	
        #Convert it to base64 so we can store it in Odoo
        create_dict['media'] = base64.b64encode( create_dict['media'] )

        _logger.error(create_dict)
        self.env['voip.call'].create(create_dict)        

    def invite_listener(self, bind_port):

        try:

            #Set the environment before starting the main thread
            with api.Environment.manage():
                #As this function is in a new thread, i need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()                
                self = self.with_env(self.env(cr=new_cr))

                _logger.error("Listen for invites on " + str(bind_port))

                local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')
        
                sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sipsocket.bind(('', bind_port))

                stage = "WAITING"
                while stage == "WAITING":
                    sipsocket.settimeout(60)
                    data, addr = sipsocket.recvfrom(2048)

                    _logger.error(data)
 
                    #Send auth response if challenged
                    if data.startswith("INVITE"):
                        _logger.error("GOT INVITE")

                        call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
                        _logger.error(call_id)
                        from_address = re.findall(r'From: (.*?);', data)[0]
                        _logger.error(from_address)

                        reply = ""
                        reply += "SIP/2.0 180 Ringing\r\n"
                        for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
                            reply += "Via: " + via_heading + "\r\n"
                        record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                        reply += "Record-Route: " + record_route + "\r\n"
                        reply += "Contact: <sip:" + self.address + "@" + local_ip + ":" + str(bind_port) + ";rinstance=0bd6d48a7ed3b6df>\r\n"                        
                        reply += "To: <sip:" + from_address + ">;tag=e856725d\r\n"
                        reply += "From: " + self.address + ";tag=8861321\r\n"
                        reply += "Call-ID: " + call_id + "\r\n"
                        reply += "CSeq: 2 INVITE\r\n"
                        reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                        reply += "Allow-Events: talk, hold\r\n"
                        reply += "Content-Length: 0\r\n"
                        reply += "\r\n"
                        
                        sipsocket.sendto(reply, addr)
                        
                        media_port = random.randint(55000,56000)
                        
                        audio_stream = base64.decodestring(self.media)
                        
                        send_media_port = re.findall(r'm=audio (.*?) RTP', data)[0]
                        _logger.error(send_media_port)
                        
                        rtp_ip = re.findall(r'\*(.*?)!', data)[0]
                        _logger.error(rtp_ip)
                
                        caller_addr = (rtp_ip, int(send_media_port) )
                        rtc_sender_starter = threading.Thread(target=self.rtp_server_sender, args=(media_port, audio_stream, caller_addr,))
                        rtc_sender_starter.start()

                        sdp = ""
                        sdp += "v=0\r\n"
                        sdp += "o=- 1759479422 3 IN IP4 " + local_ip + "\r\n"
                        sdp += "s=X-Lite release 5.0.1 stamp 86895\r\n"
                        sdp += "c=IN IP4 " + local_ip + "\r\n"
                        sdp += "t=0 0\r\n"
                        sdp += "m=audio " + str(media_port) + " RTP/AVP " + str(self.codec_id.payload_type) + "\r\n"
                        sdp += "a=sendrecv\r\n"
                        
                        reply = ""
                        reply += "SIP/2.0 200 OK\r\n"
                        for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
                            reply += "Via: " + via_heading + "\r\n"
                        record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
                        reply += "Record-Route: " + record_route + "\r\n"
                        reply += "Contact: <sip:" + self.address + "@" + local_ip + ":" + str(bind_port) + ";rinstance=0bd6d48a7ed3b6df>\r\n"
                        reply += "To: <sip:" + self.address + ">;tag=c8ff7c15\r\n"
                        reply += "From: " + from_address + ";tag=8491272\r\n"
                        reply += "Call-ID: " + str(call_id) + "\r\n"
                        reply += "CSeq: 2 INVITE\r\n"
                        reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                        reply += "Content-Type: application/sdp\r\n"
                        reply += "Supported: replaces\r\n"
                        reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                        reply += "Content-Length: " + str(len(sdp)) + "\r\n"
                        reply += "\r\n"
                        reply += sdp

                        sipsocket.sendto(reply, addr)                
                
                self._cr.close()
                    
        except Exception as e:
            _logger.error(e)            
    
    def send_register(self):
  
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sipsocket.bind(('', 0))
        bind_port = sipsocket.getsockname()[1]
        from_tag = random.randint(8000000,9000000)
        
        register_string = ""
        register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(bind_port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":" + str(bind_port) + ">\r\n" #:54443 XOR port mapping?
        register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">\r\n"
        #register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=" + str(from_tag) + "\r\n"
        register_string += "Call-ID: " + self.env.cr.dbname + "-account-" + str(self.id) + "\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        #register_string += "Expires: 3600\r\n"
        register_string += "Expires: 60\r\n"
        register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"

        _logger.error("REGISTER: " + register_string)
        
        sipsocket.sendto(register_string, (self.outbound_proxy, 5060) )

        stage = "WAITING"
        while stage == "WAITING":
            sipsocket.settimeout(10)
            data, addr = sipsocket.recvfrom(2048)

            _logger.error(data)
 
            #Send auth response if challenged
            if data.split("\r\n")[0] == "SIP/2.0 401 Unauthorized":

                authheader = re.findall(r'WWW-Authenticate: (.*?)\r\n', data)[0]
                        
                realm = re.findall(r'realm="(.*?)"', authheader)[0]
                method = "REGISTER"
                uri = "sip:" + self.domain
                nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                qop = re.findall(r'qop="(.*?)"', authheader)[0]
                nc = "00000001"
                cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])

                #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                A1 = self.auth_username + ":" + realm + ":" + self.password
                A2 = method + ":" + uri
                response = self.KD( self.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + self.H(A2) )

                register_string = ""
                register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
                register_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(bind_port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
                register_string += "Max-Forwards: 70\r\n"
                register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":" + str(bind_port) + ">\r\n" #:54443 XOR port mapping?
                register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">\r\n"
                #register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
                register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=" + str(from_tag) + "\r\n"
                register_string += "Call-ID: " + self.env.cr.dbname + "-account-" + str(self.id) + "\r\n"
                register_string += "CSeq: 2 REGISTER\r\n"
                #register_string += "Expires: 3600\r\n"
                register_string += "Expires: 60\r\n"
                register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
                register_string += 'Authorization: Digest username="' + self.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + self.domain + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                register_string += "Content-Length: 0\r\n"
                register_string += "\r\n"
        
                _logger.error(register_string)
        
                sipsocket.sendto(register_string, (self.outbound_proxy, 5060) )
            elif data.split("\r\n")[0] == "SIP/2.0 200 OK":
                _logger.error("REGISTERED")
                #Start a new thread so we can listen for invites

                invite_listener_starter = threading.Thread(target=self.invite_listener, args=(bind_port,))
                invite_listener_starter.start()
        
                stage = "REGISTERED"
                return True