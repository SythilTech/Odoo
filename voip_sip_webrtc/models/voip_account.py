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
import sys
import datetime
import struct
import base64
from . import sdp
from . import sip
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
    bind_port = fields.Integer(string="Bind Port")
    action_id = fields.Many2one('voip.account.action', string="Call Action")
    call_dialog_id = fields.Many2one('voip.dialog', string="Call Dialog")
    bind_port = fields.Integer(string="Bind Port", help="A record of what port the SIP session is bound on so we can deregister if neccassary")

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

    def generate_rtp_packet(self, rtp_payload_data, payload_type, payload_size, packet_count, sequence_number, timestamp):

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
            rtp_data += " " + format( payload_type, '02x')

        rtp_data += " " + format( sequence_number, '04x')

        rtp_data += " " + format( int(timestamp), '08x')

        #Synchronization Source identifier: 0x1202763d
        rtp_data += " 12 20 76 3d"

        #Payload:
        hex_string = ""
        for rtp_char in rtp_payload_data:
            hex_format = "{0:02x}".format(rtp_char)
            hex_string += hex_format + " "

        rtp_data += " " + hex_string
        return bytes.fromhex( rtp_data.replace(" ","") )

    def rtp_server_listener(self, q, rtc_sender_thread, rtpsocket, voip_call_client_id, call_action_id, model=False, record_id=False):
        #Create the call with the audio
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            audio_stream = b''
            call_start_time = datetime.datetime.now()
            current_call_action = self.env['voip.account.action'].browse( int(call_action_id) )

            try:

                #Call starts now
                #voip_call_client = self.env['voip.call.client'].browse( int(voip_call_client_id) )
                #voip_call_client.vc_id.write({'status':"active", 'start_time': datetime.datetime.now()})

                _logger.error("Start RTP Listening")

                t = threading.currentThread()
                while getattr(t, "stream_active", True):

                    rtpsocket.settimeout(10)
                    data, addr = rtpsocket.recvfrom(2048)
                    
                    #_logger.error(data.hex())
                    payload_type = data[1]
                    
                    #Listen for telephone events DTMF
                    if payload_type == 101:
                        _logger.error("Telephone Event")
                        dtmf_number = data[12]
                        _logger.error(dtmf_number)
                        dmtf_transition = self.env['voip.account.action.transition'].search([('action_from_id','=', current_call_action.id), ('trigger','=','dtmf'), ('dtmf_input','=',dtmf_number)])
                        
                        if dmtf_transition:
                            current_call_action = dmtf_transition.action_to_id
                        
                            #Also set the current_call_action of the sending thread
                            q.put(current_call_action)
                    
                    #Add the RTP payload to the received data
                    audio_stream += data[12:]

            except Exception as e:
                #Timeout
                _logger.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                
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
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error("Line: " + str(exc_tb.tb_lineno) )


    def rtp_server_sender(self, q, rtpsocket, rtp_ip, rtp_port, media_data, codec_id, voip_call_client_id, call_action_id):

        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            
            try:

                server_stream_data = ""

                _logger.error("Start RTP Sender")

                current_call_action = self.env['voip.account.action'].browse( int(call_action_id) )
                codec = self.env['voip.codec'].browse( int(codec_id) )

                packet_count = 0
                media_index = 0
                sequence_number = randint(29161, 30000)
                timestamp = (datetime.datetime.utcnow() - datetime.datetime(1900, 1, 1, 0, 0, 0)).total_seconds()

                t = threading.currentThread()
                while getattr(t, "stream_active", True):

                    method = '_voip_action_sender_%s' % (current_call_action.action_type_id.internal_name,)
                    action = getattr(current_call_action, method, None)

                    #The call action is capable of changing the media playback point (reset media from start) and changing the current call action (DTMF)
                    rtp_payload_data, media_data, media_index = action(media_data, media_index, codec.payload_size)

                    if packet_count < 10:
                        _logger.error(rtp_payload_data)
                        _logger.error(media_index)

                    send_data = self.generate_rtp_packet(rtp_payload_data, codec.payload_type, codec.payload_size, packet_count, sequence_number, timestamp)
                    rtpsocket.sendto(send_data, (rtp_ip, rtp_port) )

                    packet_count += 1
                    sequence_number += 1
                    #timestamp += codec.sample_rate / (1000 / codec.sample_interval)
                    timestamp = (datetime.datetime.utcnow() - datetime.datetime(1900, 1, 1, 0, 0, 0)).total_seconds()
                    
                    try:
                        current_call_action = q.get(True, 0.02)
                        _logger.error("Current Action Change")
                        _logger.error(current_call_action.name)
                        media_data = base64.decodestring(current_call_action.recorded_media_id.media)
                        media_index = 0
                    except:
                        pass

            except Exception as e:
                #Timeout
                _logger.error(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error("Line: " + str(exc_tb.tb_lineno) )

        
            #try:
                #Add the stream data to the call
            #    voip_call_client = self.env['voip.call.client'].browse( int(voip_call_client_id) )
            #    voip_call_client.vc_id.write({'server_stream_data': base64.b64encode(server_stream_data)})
            #except Exception as e:
            #    _logger.error(e)
            #    exc_type, exc_obj, exc_tb = sys.exc_info()
            #    _logger.error("Line: " + str(exc_tb.tb_lineno) )

    def call_accepted(self, session, data):
        _logger.error("Call Accepted")

        with api.Environment.manage():
            #As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
            call_to_full = re.findall(r'To: (.*?)\r\n', data)[0]
            call_to = re.findall(r'<sip:(.*?):', call_to_full)[0]

            voip_call = self.env['voip.call'].search([('sip_call_id','=', call_id)])[0]

            #Setup the first action for an outgoing call
            start_call_action = self.env['voip.account.action'].search([('voip_dialog_id','=', voip_call.call_dialog_id.id), ('start','=',True)])[0]
            method = '_voip_action_outgoing_setup_%s' % (start_call_action.action_type_id.internal_name,)
            action = getattr(start_call_action, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

            action(session, data)            
            
            self._cr.close()

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

    def make_call(self, to_address, call_dialog, model=False, record_id=False):

        audio_media_port = random.randint(55000,56000)
        local_ip = self.env['ir.default'].get('voip.settings', 'server_ip')

        if "@" not in to_address:
            to_address = to_address + "@" + self.domain

        ulaw_codec = self.env['ir.model.data'].get_object('voip_sip_webrtc','pcmu')

        call_sdp = sdp.generate_sdp(self, local_ip, audio_media_port, [ulaw_codec.payload_type])

        sip_session = sip.SIPSession(local_ip, self.username, self.domain, self.password, self.auth_username, self.outbound_proxy, self.port, self.voip_display_name)
        sip_session.call_accepted += self.call_accepted
        sip_session.call_rejected += self.call_rejected
        sip_session.call_ended += self.call_ended
        sip_session.call_error += self.call_error
        call_id = sip_session.send_sip_invite(to_address, call_sdp)

        #Create the call now so we can mark it has missed or rejected
        create_dict = {'from_address': self.address, 'to_address': to_address, 'to_audio': '', 'codec_id': ulaw_codec.id, 'ring_time': datetime.datetime.now(), 'sip_call_id': call_id, 'call_dialog_id': call_dialog.id}
        voip_call = self.env['voip.call'].create(create_dict)

        #Also create the client list
        voip_call_client = self.env['voip.call.client'].create({'vc_id': voip_call.id, 'audio_media_port': audio_media_port, 'sip_address': to_address, 'name': to_address, 'model': model, 'record_id': record_id})

    def message_sent(self, session, data):
        _logger.error("Message Sent")

    def send_message(self, to_address, message_body, model=False, record_id=False):

        local_ip = self.env['ir.default'].get('voip.settings', 'server_ip')

        sip_session = sip.SIPSession(local_ip, self.username, self.domain, self.password, self.auth_username, self.outbound_proxy, self.port, self.voip_display_name)
        sip_session.message_sent += self.message_sent
        call_id = sip_session.send_sip_message(to_address, message_body)

        if model:
            self.env[model].browse( int(record_id) ).message_post(body=message_body, subject="SIP Message Sent", message_type="comment", subtype='voip_sip_webrtc.voip_call')

        return "OK"

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

            #The setup action is only executed for the first action, e.g. call media only accepts the call first but if used in a chain it just plays
            #Not all actions will autoaccept the call for example call users will wait for a answer
            #Find the first action in the call dialog
            start_call_action = self.env['voip.account.action'].search([('voip_dialog_id','=', voip_account.call_dialog_id.id), ('start','=',True)])[0]
            method = '_voip_action_incoming_setup_%s' % (start_call_action.action_type_id.internal_name,)
            action = getattr(start_call_action, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

            action(session, data)

            self._cr.close()

    def message_received(self, session, data, message):
        _logger.error("Message Received")
        _logger.error(message)

    def register_ok(self, session, data):
        _logger.error("REGISTER OK")

        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            voip_account = self.env['voip.account'].search([('username','=',session.username), ('domain','=',session.domain)])[0]
            voip_account.state = "active"
            voip_account.bind_port = session.bind_port

            self._cr.commit()
            self._cr.close()
        
    sip_session = ""
    def uac_register(self):

        local_ip = self.env['ir.default'].get('voip.settings', 'server_ip')

        if local_ip:
            sip_session = sip.SIPSession(local_ip, self.username, self.domain, self.password, self.auth_username, self.outbound_proxy, self.port, self.voip_display_name)
            sip_session.call_ringing += self.call_ringing
            sip_session.message_received += self.message_received
            sip_session.register_ok += self.register_ok
            sip_session.send_sip_register(self.address)
        else:
            raise UserError("Please enter your IP under settings first")

    def uac_deregister(self):
        _logger.error("DEREGISTER")