# -*- coding: utf-8 -*-
from openerp.http import request
import datetime
import logging
import socket
import threading
_logger = logging.getLogger(__name__)
import time
from random import randint
from hashlib import sha1
import ssl
#from dtls import do_patch
#from dtls.sslconnection import SSLConnection
import hmac
import hashlib
import random
import string
import passlib
import struct
import zlib
import re
from openerp.exceptions import UserError
import binascii
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import api, fields, models

class VoipCall(models.Model):

    _name = "voip.call"
    _order = 'create_date desc'

    from_address = fields.Char(string="From Address")
    from_partner_id = fields.Many2one('res.partner', string="From Partner", help="From can be blank if the call comes from outside of the system")
    from_partner_sdp = fields.Text(string="From Partner SDP")
    partner_id = fields.Many2one('res.partner', string="(OBSOLETE)To Partner")
    to_address = fields.Char(string="To Address")
    to_partner_id = fields.Many2one('res.partner', string="To Partner", help="To partner can be blank if the source is external and no record with mobile or sip is found")
    status = fields.Selection([('pending','Pending'), ('missed','Missed'), ('accepted','Accepted'), ('rejected','Rejected'), ('active','Active'), ('over','Complete'), ('failed','Failed'), ('busy','Busy'), ('cancelled','Cancelled')], string='Status', default="pending", help="Pending = Calling person\nActive = currently talking\nMissed = Call timed out\nOver = Someone hit end call\nRejected = Someone didn't want to answer the call")
    ring_time = fields.Datetime(string="Ring Time", help="Time the call starts dialing")
    start_time = fields.Datetime(string="Start Time", help="Time the call was answered (if answered)")
    end_time = fields.Datetime(string="End Time", help="Time the call end")
    duration = fields.Char(string="Duration", help="Length of the call")
    transcription = fields.Text(string="Transcription", help="Automatic transcription of the call")
    notes = fields.Text(string="(OBSOLETE)Notes", help="Additional comments outside the transcription (use the chatter instead of this field)")
    client_ids = fields.One2many('voip.call.client', 'vc_id', string="Client List")
    type = fields.Selection([('internal','Internal'),('external','External')], string="Type")
    mode = fields.Selection([('videocall','video call'), ('audiocall','audio call'), ('screensharing','screen sharing call')], string="Mode", help="This is only how the call starts, i.e a video call can turn into a screen sharing call mid way")
    sip_tag = fields.Char(string="SIP Tag")
    voip_account = fields.Many2one('voip.account', string="VOIP Account")
    to_audio = fields.Binary(string="Audio")
    to_audio_filename = fields.Char(string="(OBSOLETE)Audio Filename")
    media = fields.Binary(string="Media")
    media_filename = fields.Char(string="Media Filename")
    server_stream_data = fields.Binary(string="Server Stream Data", help="Stream data sent by the server, e.g. automated call")    
    media_url = fields.Char(string="Media URL", compute="_compute_media_url")
    codec_id = fields.Many2one('voip.codec', string="Codec")
    direction = fields.Selection([('internal','Internal'), ('incoming','Incoming'), ('outgoing','Outgoing')], string="Direction")
    sip_call_id = fields.Char(string="SIP Call ID")
    ice_username = fields.Char(string="ICE Username")
    ice_password = fields.Char(string="ICE Password")
    twilio_sid = fields.Char(string="Twilio SID")
    twilio_account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    currency_id = fields.Many2one('res.currency', string="Currency")
    price = fields.Float(string="Price")
    margin = fields.Float(string="Margin")

    @api.one
    def _compute_media_url(self):
        if self.media:
            self.media_url = "/voip/messagebank/" + str(self.id)
        else:
            self.media_url = ""

    @api.model
    def clear_messagebank(self):
        """ Delete recorded phone call to clear up space """

        for voip_call in self.env['voip.call'].search([('to_audio','!=', False)]):
            #TODO remove to_audio
            voip_call.to_audio = False
            voip_call.to_audio_filename = False

            voip_call.server_stream_data = False

            voip_call.media = False
            voip_call.media_filename = False

        #Also remove the media attached to the client
        for voip_client in self.env['voip.call.client'].search([('audio_stream','!=', False)]):
            voip_client.audio_stream = False

    def start_call(self):
        """ Process the ICE queue now """

        #Notify caller and callee that the call was rejected
        for voip_client in self.client_ids:
            notification = {'call_id': self.id}
            self.env['bus.bus'].sendone((request._cr.dbname, 'voip.start', voip_client.partner_id.id), notification)

    def accept_call(self):
        """ Mark the call as accepted and send response to close the notification window and open the VOIP window """

        if self.status == "pending":
            self.status = "accepted"

        #Notify caller and callee that the call was accepted
        for voip_client in self.client_ids:
            notification = {'call_id': self.id, 'status': 'accepted', 'type': self.type}
            self.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)            

    def reject_call(self):
        """ Mark the call as rejected and send the response so the notification window is closed on both ends """

        if self.status == "pending":
            self.status = "rejected"

        #Notify caller and callee that the call was rejected
        for voip_client in self.client_ids:
            notification = {'call_id': self.id, 'status': 'rejected'}
            self.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)

    def miss_call(self):
        """ Mark the call as missed, both caller and callee will close there notification window due to the timeout """

        if self.status == "pending":
            self.status = "missed"

    def begin_call(self):
        """ Mark the call as active, we start recording the call duration at this point """

        if self.status == "accepted":
            self.status = "active"

        self.start_time = datetime.datetime.now()

    def end_call(self):
        """ Mark the call as over, we can calculate the call duration based on the start time, also send notification to both sides to close there VOIP windows """

        if self.status == "active":
            self.status = "over"

            self.end_time = datetime.datetime.now()
            diff_time = datetime.datetime.strptime(self.end_time, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)
            self.duration = str(diff_time.seconds) + " Seconds"

        #Notify both caller and callee that the call is ended
        for voip_client in self.client_ids:
            notification = {'call_id': self.id}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.end', voip_client.partner_id.id), notification)

    def voip_call_sdp(self, sdp):
        """Store the description and send it to everyone else"""

        if self.type == "internal":
            for voip_client in self.client_ids:
                if voip_client.partner_id.id == self.env.user.partner_id.id:
                    voip_client.sdp = sdp
                else:
                    notification = {'call_id': self.id, 'sdp': sdp }
                    self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)

    def generate_call_sdp(self):

        sdp_response = ""

        #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
        sdp_response += "v=0\r\n"

        #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2 (Should come up with a better session id...)
        sess_id = int(time.time()) #Not perfect but I don't expect more then one call a second
        sess_version = 0 #Will always start at 0
        sdp_response += "o=- " + str(sess_id) + " " + str(sess_version) + " IN IP4 0.0.0.0\r\n"        

        #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3 (We don't need a session name, information about the call is all displayed in the UI)
        sdp_response += "s= \r\n"

        #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9 (For now sessions are infinite but we may use this if for example a company charges a price for a fixed 30 minute consultation)
        sdp_response += "t=0 0\r\n"

        #In later versions we might send the missed call mp3 via rtp
        sdp_response += "a=sendrecv\r\n"

        #TODO generate cert/fingerprint within module
        fignerprint = self.env['ir.values'].get_default('voip.settings', 'fingerprint')
        sdp_response += "a=fingerprint:sha-256 " + fignerprint + "\r\n"
        sdp_response += "a=setup:passive\r\n"

        #Sure why not
        sdp_response += "a=ice-options:trickle\r\n"

        #Sigh no idea
        sdp_response += "a=msid-semantic:WMS *\r\n"

        #Random stuff, left here so I don't have get it a second time if needed
        #example supported audio profiles: 109 9 0 8 101
        #sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF 109 101\r\n"

        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        audio_codec = "9" #Use G722 Audio Profile
        sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF " + audio_codec + "\r\n"

        #Connection Data ("c=") https://tools.ietf.org/html/rfc4566#section-5.7 (always seems to be 0.0.0.0?)
        sdp_response += "c=IN IP4 0.0.0.0\r\n"

        #ICE creds (https://tools.ietf.org/html/rfc5245#page-76)
        ice_ufrag = ''.join(random.choice('123456789abcdef') for _ in range(4))
        ice_pwd = ''.join(random.choice('123456789abcdef') for _ in range(22))
        self.ice_password = ice_pwd
        sdp_response += "a=ice-ufrag:" + str(ice_ufrag) + "\r\n"
        sdp_response += "a=ice-pwd:" + str(ice_pwd) + "\r\n"

        #Ummm naming each media?!?
        sdp_response += "a=mid:sdparta_0\r\n"
            
        return {"type":"answer","sdp": sdp_response}

    def message_bank(self, sdp):

        _logger.error("Message Bank")

        #Ideally an integrity check should be done to ensure binding requests are valid, this is particiularly an issue for http since the random port can be sniffed.
        #result = re.search('\r\na=ice-pwd:(.*)\r\n', sdp['sdp'])
        #ice_password = result.group(1)

        server_sdp = self.generate_call_sdp()

        notification = {'call_id': self.id, 'sdp': server_sdp }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', self.from_partner_id.id), notification)

        #RTP
        #port = 62382
        #Random even number
        port = randint(16384 /2, 32767 / 2) * 2
        server_ice_candidate = self.env['voip.server'].generate_server_ice(port, 1)
        self.start_rtc_listener(port, "RTP")
        notification = {'call_id': self.id, 'ice': server_ice_candidate }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', self.from_partner_id.id), notification)

        #RTCP
        port += 1
        server_ice_candidate = self.env['voip.server'].generate_server_ice(port, 2)
        self.start_rtc_listener(port, "RTCP")
        notification = {'call_id': self.id, 'ice': server_ice_candidate }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', self.from_partner_id.id), notification)

    def voip_call_ice(self, ice):
        """Forward ICE to everyone else"""

        for voip_client in self.client_ids:

            #Don't send ICE back to yourself
            if voip_client.partner_id.id != self.env.user.partner_id.id:
                notification = {'call_id': self.id, 'ice': ice }
                self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)        

    def close_message_bank(self):

        #Notify the caller that the call is ended due to message bank timeout
        notification = {'call_id': self.id}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.end', self.from_partner_id.id), notification)

        #TODO trancode G722 to a format that can be listened to within a browser

        #TODO save the transcoded file to the call so it can be listened to later (Only keep for 48 hours to save space also legal requirements in some places)

    def webrtc_dtls_handshake(self):
        #Stage 2 DTLS
        _logger.error("DTLS INCOMPLETE")

    def rtp_stun_listener(self, d, client_ip, port):

        if d[1] == "00" and d[2] == "01":
            message_type = "Binding Request"

        message_length = int( d[3] + d[4], 16)
        message_cookie = ' '.join(d[5:9])
        transaction_id = ' '.join(d[9:21])

        #----Compose binding request-----
        send_data = ""

        #Message Type (Binding Success Response)
        send_data += "01 01"

        #Message Length (In this controlled environment it will always be 44)
        send_data += " 00 2C"

        #Magic Cookie (always set to 0x2112A442)
        send_data += " 21 12 a4 42"

        #96 bit (12 byte) transaction ID (has to be the same as the bind request)
        send_data += transaction_id

        #XOR mapped address attribute
        send_data += " 00 20"

        #Attribute Length (fixed 8 for IPv4, IPv6 will increase this)
        send_data += " 00 08"

        #Reservered (reserved for what...)
        send_data += " 00"

        #Protocol Family (Always IPv4 for now...)
        send_data += " 01"

        #Port XOR
        client_port = port
        send_data += " " + format( client_port ^ 0x2112 , '04x')

        #IP XOR-d
        client_ip_int = struct.unpack("!I", socket.inet_aton(client_ip))[0]
        send_data += " " + format( client_ip_int ^ 0x2112A442 , '08x')

        #Cut off header
        hmac_input = send_data.replace(" ","")[8:]

        #Readd header but subtract 8 from length before calculating hmac
        hmac_input = "01010024" + hmac_input

        stun_password = self.ice_password

        key = passlib.utils.saslprep( stun_password )

        mess_hmac = hmac.new( str(key), msg=hmac_input.decode("hex"), digestmod=hashlib.sha1).digest().encode('hex')

        #Message Integrity Attribute
        send_data += " 00 08"

        #Attribute Length (Always 20 bytes)
        send_data += " 00 14"

        #HMAC-SHA1
        send_data += mess_hmac

        crc32_int = binascii.crc32( binascii.a2b_hex(  send_data.replace(" ","") ) )  % (1<<32)
        crc_hex = format( crc32_int ^ 0x5354554e, '08x')

        #Fingerprint Attribute
        send_data += " 80 28"

        #Atrribute Length (CRC-32 is always 4 bytes)
        send_data += " 00 04"

        #Fingerprint
        send_data += " " + crc_hex

        #Ok now convert it back so we can send it
        return send_data.replace(" ","").decode('hex')

    def rtp_server_listener(self, port, message_bank_duration):

        #First Message we get is the conectivity test (STUN Binding Request User)

        #Second is DTLSv1.2 or more specifically dtls-strp

        #3rd is the stream with the G722 Audio payload

        _logger.error("Start RTP Listening on Port " + str(port) )

        stunsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        stunsocket.bind(('', port));

        start = time.time()
        stage = "STUN"
        hex_string = ""

        #Code is easier to understand if we start at 1 rather then 0...
        hex_data = ['FF']

        #Stage 1 STUN Connectivity Test
        while stage == "STUN" or stage == "DTLS HELLO":

            data, addr = stunsocket.recvfrom(2048)

            #Convert to hex so we can human interpret each byte
            for rtp_char in data:
                hex_format = "{0:02x}".format(ord(rtp_char))
                hex_data.append(hex_format)
                hex_string += hex_format + " "

            _logger.error("HEX DATA: " + hex_string)

            if stage == "STUN":
                send_data = self.rtp_stun_listener(hex_data, addr[0], port)
                stunsocket.sendto(send_data, addr )
                #We don't get any acknowledgement so we just assume everything went fine...
                stage = "DTLS HELLO"
            else:
                send_data = self.webrtc_dtls_handshake()
                stunsocket.sendto(send_data, addr )
                stage = "DTLS CIPHER"

        _logger.error("DTLS Stage")

        #Stage 2 DTLS (TODO)

        #End the call and do any post call processing
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))

            self.close_message_bank()

            #Have to manually commit the new cursor?
            self.env.cr.commit()

            self._cr.close()

        _logger.error("END MESSAGE BANK")

    def start_rtc_listener(self, port, mode):

        message_bank_duration = self.env['ir.values'].get_default('voip.settings', 'message_bank_duration')

        #Start a new thread so you don't block the main Odoo thread
        if mode is "RTP":
            rtc_listener_starter = threading.Thread(target=self.rtp_server_listener, args=(port,message_bank_duration,))
            rtc_listener_starter.start()
        elif mode is "RTCP":
            #For now we don't use RTCP...
            rtc_listener_starter = threading.Thread(target=self.rtp_server_listener, args=(port,message_bank_duration,))
            rtc_listener_starter.start()

class VoipCallClient(models.Model):

    _name = "voip.call.client"

    vc_id = fields.Many2one('voip.call', string="VOIP Call")
    partner_id = fields.Many2one('res.partner', string="Partner")
    sip_address = fields.Char(string="SIP Address")
    name = fields.Char(string="Name", help="Can be a number if the client is from outside the system")
    model = fields.Char(string="Model")
    record_id = fields.Integer(string="Record ID")
    state = fields.Selection([('invited','Invited'),('joined','joined'),('media_access','Media Access')], string="State", default="invited")
    sdp = fields.Char(string="SDP")
    sip_invite = fields.Char(string="SIP INVITE Message")
    sip_addr = fields.Char(string="Address")
    sip_addr_host = fields.Char(string="SIP Address Host")
    sip_addr_port = fields.Char(string="SIP Address Port")
    audio_media_port = fields.Integer(string="Audio Media Port")
    audio_stream = fields.Binary(string="Audio Stream")