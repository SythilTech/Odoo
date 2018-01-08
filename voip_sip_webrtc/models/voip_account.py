# -*- coding: utf-8 -*-
import socket
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from openerp.http import request
import re
import hashlib
import random
from openerp import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import threading
from threading import Timer
import time
from time import sleep
import datetime
import struct
import base64
import sdp
import sip
from random import randint
            
class VoipAccount(models.Model):

    _name = "voip.account"

    name = fields.Char(string="Name", required="True")
    state = fields.Selection([('new','New'), ('inactive','Inactive'), ('active','Active')], default="new", string="State")
    type = fields.Selection([('sip', 'SIP'), ('xmpp', 'XMPP')], default="sip", string="Account Type")
    address = fields.Char(string="SIP Address", required="True")
    password = fields.Char(string="SIP Password", required="True")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username", required="True")
    domain = fields.Char(string="Domain", required="True")
    voip_display_name = fields.Char(string="Display Name", default="Odoo")
    outbound_proxy = fields.Char(string="Outbound Proxy")
    port = fields.Integer(string="Port", default="5060")
    verified = fields.Boolean(string="Verified")
    wss = fields.Char(string="WSS", default="wss://edge.sip.onsip.com")
    gsm_media = fields.Binary(string="(OBSOLETE)GSM Audio File")
    media = fields.Binary(string="(OBSOLETE)Raw Audio File")
    codec_id = fields.Many2one('voip.codec', string="(OBSOLETE)Codec")
    bind_port = fields.Integer(string="Bind Port")
    action_id = fields.Many2one('voip.account.action', string="Call Action")
    action_ids = fields.One2many('voip.account.action', 'account_id', string="Call Actions")

    @api.onchange('username','domain')
    def _onchange_username(self):
        if self.username and self.domain:
            self.address = self.username + "@" + self.domain

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
    
    def generate_rtp_packet(self, audio_stream, codec_id, packet_count, sequence_number, timestamp):

        rtp_data = ""

        #---- Compose RTP packet to send back---
        #10.. .... = Version: RFC 1889 Version (2)
        #..0. .... = Padding: False
        #...0 .... = Extension: False
        #.... 0000 = Contributing source identifiers count: 0
        rtp_data += "80"

        #0... .... = Marker: False
        #Payload type
        if packet_count == 0:
            #ulaw
            rtp_data += " 80"
        else:
            rtp_data += " " + format( codec_id.payload_type, '02x')

        rtp_data += " " + format( sequence_number, '04x')
        
        rtp_data += " " + format( int(timestamp), '08x')
            
        #Synchronization Source identifier: 0x1202763d
        rtp_data += " 12 20 76 3d"

        #Payload:
        payload_data = audio_stream[packet_count * codec_id.payload_size : packet_count * codec_id.payload_size + codec_id.payload_size]
        hex_string = ""

        for rtp_char in payload_data:
            hex_format = "{0:02x}".format(ord(rtp_char))
            hex_string += hex_format + " "

        rtp_data += " " + hex_string
        return rtp_data.replace(" ","").decode('hex')
            
    def rtp_server_listener(self, rtc_sender_thread, rtpsocket, voip_call_client_id, model=False, record_id=False):
        #Create the call with the audio
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            
            audio_stream = ""
            call_start_time = datetime.datetime.now()            
            
            try:

                #Call starts now
                #voip_call_client = self.env['voip.call.client'].browse( int(voip_call_client_id) )
                #voip_call_client.vc_id.write({'status':"active", 'start_time': datetime.datetime.now()})
                
                _logger.error("Start RTP Listening")

                t = threading.currentThread()                            
                while getattr(t, "stream_active", True):

                    rtpsocket.settimeout(10)
                    data, addr = rtpsocket.recvfrom(2048)
                    #Add the RTP payload to the received data
                    audio_stream += data[12:]

            except Exception as e:
                #Timeout
                _logger.error(e)

            try:
                
                #Update call after the stream times out
                voip_call_client = self.env['voip.call.client'].browse( int(voip_call_client_id) )
                voip_call_client.vc_id.write({'media': base64.b64encode(audio_stream), 'status': 'over', 'media_filename': "call.raw", 'start_time': call_start_time, 'end_time': datetime.datetime.now()})
                diff_time = datetime.datetime.now() - call_start_time
                voip_call_client.vc_id.duration = str(diff_time.seconds) + " Seconds"
                
                #Add the stream data to this client
                voip_call_client.write({'audio_stream': base64.b64encode(audio_stream)})

                #Have to manually commit the new cursor?
                self._cr.commit()
                self._cr.close()
            
                #if model:
                #    self.env[model].browse( int(record_id) ).message_post(body="Call Made", subject="Call Made", message_type="comment", subtype='voip_sip_webrtc.voip_call')
                
                #Kill the sending thread
                rtc_sender_thread.stream_active = False
                rtc_sender_thread.join()
                                
            except Exception as e:
                _logger.error(e)


    def rtp_server_sender(self, rtpsocket, rtp_ip, rtp_port, audio_stream, codec_id, voip_call_client_id):

        #Create the call with the audio
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
        
            server_stream_data = ""
        
            try:

                packet_count = 0
                sequence_number = randint(29161, 30000)
                timestamp = (datetime.datetime.utcnow() - datetime.datetime(1900, 1, 1, 0, 0, 0)).total_seconds()                
                
                t = threading.currentThread()
                while getattr(t, "stream_active", True):
            
                    #Send audio data out every 20ms
                    server_stream_data += audio_stream[packet_count * codec_id.payload_size : packet_count * codec_id.payload_size + codec_id.payload_size]

                    send_data = self.generate_rtp_packet(audio_stream, codec_id, packet_count, sequence_number, timestamp)
                    rtpsocket.sendto(send_data, (rtp_ip, rtp_port) )

                    packet_count += 1
                    sequence_number += 1
                    timestamp += codec_id.sample_rate / (1000 / codec_id.sample_interval)
                    sleep(0.02)

            except Exception as e:
                #Sudden Disconnect
                _logger.error(e)

            try:
                #Add the stream data to the call
                voip_call_client = self.env['voip.call.client'].browse( int(voip_call_client_id) )
                voip_call_client.vc_id.write({'server_stream_data': base64.b64encode(server_stream_data)})                    
            except Exception as e:
                _logger.error(e)

            #Have to manually commit the new cursor?
            self.env.cr.commit()
        
            self._cr.close()    
            
    def call_accepted(self, session, data):
        _logger.error("Call Accepted")

        with api.Environment.manage():
	    #As this function is in a new thread, i need to open a new cursor, because the old one may be closed
	    new_cr = self.pool.cursor()                
            self = self.with_env(self.env(cr=new_cr))
            
            call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
            call_to_full = re.findall(r'To: (.*?)\r\n', data)[0]
            call_to = re.findall(r'<sip:(.*?):', call_to_full)[0]
            
            voip_call = self.env['voip.call'].search([('sip_call_id','=', call_id)])[0]
            
            #Find the voip client to the call was to
            voip_call_client = self.env['voip.call.client'].search([('vc_id','=', voip_call.id), ('sip_address','=', call_to)])[0]
        
            rtp_ip = re.findall(r'c=IN IP4 (.*?)\r\n', data)[0]
            rtp_port = int(re.findall(r'm=audio (.*?) RTP', data)[0])

            #The call was accepted so start listening for / sending RTP data
            rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtpsocket.bind(('', voip_call_client.audio_media_port));
        
            rtc_sender_thread = threading.Thread(target=self.rtp_server_sender, args=(rtpsocket, rtp_ip, rtp_port, voip_call.to_audio, voip_call.codec_id, voip_call_client.id,))
            rtc_sender_thread.start()

            rtc_listener_thread = threading.Thread(target=self.rtp_server_listener, args=(rtc_sender_thread, rtpsocket, voip_call_client.id, voip_call_client.model, voip_call_client.record_id,))
            rtc_listener_thread.start()

            #session.rtp_threads.append(rtc_sender_thread)
            #session.rtp_threads.append(rtc_listener_thread)
            
            #self._cr.close()
                
    def call_rejected(self, session, data):
        _logger.error("Call Rejected")

    def call_ended(self, session, data):
        _logger.error("Call Ended")
        
        for rtp_stream in session.rtp_threads:
            rtp_stream.stream_active = False
            rtp_stream.join()

    def call_error(self, session, data):
        _logger.error("Call Error")
        _logger.error(data)
        
    def make_call(self, to_address, audio_stream, audio_codec, model=False, record_id=False):

        audio_media_port = random.randint(55000,56000)
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        if "@" not in to_address:
            to_address = to_address + "@" + self.domain
            
        call_sdp = sdp.generate_sdp(self, local_ip, audio_media_port, [audio_codec.payload_type])

        sip_session = sip.SIPSession(local_ip, self.username, self.domain, self.password, self.auth_username, self.outbound_proxy, self.port, self.voip_display_name)
        sip_session.call_accepted += self.call_accepted
        sip_session.call_rejected += self.call_rejected
        sip_session.call_ended += self.call_ended
        sip_session.call_error += self.call_error
        call_id = sip_session.send_sip_invite(to_address, call_sdp)

        #Create the call now so we can make it has missed or rejected
        create_dict = {'from_address': self.address, 'to_address': to_address, 'to_audio': audio_stream, 'codec_id': audio_codec.id, 'ring_time': datetime.datetime.now(), 'sip_call_id': call_id }
        voip_call = self.env['voip.call'].create(create_dict)

        #Also create the client list
        voip_call_client = self.env['voip.call.client'].create({'vc_id': voip_call.id, 'audio_media_port': audio_media_port, 'sip_address': to_address, 'name': to_address, 'model': model, 'record_id': record_id})        
 
    def send_message(self, to_address, message_body, model=False, record_id=False):
  
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')
        
        sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sipsocket.bind(('', 0))
        bind_port = sipsocket.getsockname()[1]

        message_string = ""
        message_string += "MESSAGE sip:" + self.address + " SIP/2.0\r\n"
        message_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(bind_port) + ";branch=z9hG4bK-524287-1---60245a218c8cff0a;rport\r\n"
        message_string += "Max-Forwards: 70\r\n"
        message_string += 'To: <sip:' + to_address + ">;messagetype=IM\r\n"
        message_string += 'From: "' + self.voip_display_name + '"<sip:' + self.address + ":" + str(bind_port) + ">;tag=903df0a\r\n"
        message_string += "Call-ID: 86895YTZlZGM3MzFkZTk4MzA2NGE0NjU3ZGExNmU5NTE1ZDM\r\n"
        message_string += "CSeq: 1 MESSAGE\r\n"
        message_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        message_string += "Content-Type: text/html\r\n"
        message_string += "User-Agent: Sythil Tech SIP Client\r\n"
        message_string += "Content-Length: " + str(len(message_body)) + "\r\n"
        message_string += "\r\n"
        message_string += message_body

        send_to = ""
        if self.outbound_proxy:
            send_to = self.outbound_proxy
        else:
            send_to = self.domain
            
        _logger.error(message_string)
        sipsocket.sendto(message_string, (send_to, self.port) )
        
        #Wait and send back the auth reply
        stage = "WAITING"
        while stage == "WAITING":
            sipsocket.settimeout(10)        
            data, addr = sipsocket.recvfrom(2048)

            _logger.error(data)
            
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

                reply = message_string
                
                #Add one to sequence number
                reply = reply.replace("CSeq: 1 MESSAGE", "CSeq: 2 MESSAGE")

                #Add the Proxy Authorization line before the user agent line
                idx = reply.index("User-Agent:")
                insert_text = 'Proxy-Authorization: Digest username="' + self.auth_username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + to_address + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                reply = reply[:idx] + insert_text + reply[idx:]
                _logger.error(reply)
                sipsocket.sendto(reply, addr)
            elif data.split("\r\n")[0] == "SIP/2.0 200 OK":
                stage = "SENT"
                
                if model:
                    #Add to the chatter
                    #TODO add SIP subtype
                    self.env[model].browse( int(record_id) ).message_post(body=message_body, subject="SIP Message Sent", message_type="comment")

                return "OK"
            else:
                stage = "FAILURE"
                return data.split("\r\n")[0]

    def process_audio_stream(self, create_dict):
        _logger.error("Process File")
        	
        #Convert it to base64 so we can store it in Odoo
        create_dict['media'] = base64.b64encode( create_dict['media'] )

        _logger.error(create_dict)
        self.env['voip.call'].create(create_dict)        
        
    def call_ringing(self, session, data):
        _logger.error("Call Ringing")

        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            
            voip_account = self.env['voip.account'].search([('username','=', session.username), ('domain','=', session.domain) ])[0]

            #Execute the account action
            method = '_voip_action_%s' % (voip_account.action_id.action_type_id.internal_name,)
            action = getattr(self.action_id, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

            action(session, data)

            self._cr.close()
        
    sip_session = ""
    def uac_register(self):
    
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        sip_session = sip.SIPSession(local_ip, self.username, self.domain, self.password, self.auth_username, self.outbound_proxy, self.port, self.voip_display_name)
        sip_session.call_ringing += self.call_ringing
        sip_session.send_sip_register(self.address)