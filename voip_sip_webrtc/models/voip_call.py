# -*- coding: utf-8 -*-
from openerp.http import request
import datetime
import logging
import socket
import threading
_logger = logging.getLogger(__name__)
import time
from random import randint
import hmac
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import Crypto.Util.Counter
from OpenSSL import SSL
from OpenSSL._util import (
    ffi as _ffi,
    lib as _lib)
    
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import api, fields, models

class VoipCall(models.Model):

    _name = "voip.call"

    from_partner_id = fields.Many2one('res.partner', string="From", help="From can be blank if the call comes from outside of the system")
    partner_id = fields.Many2one('res.partner', string="To")
    status = fields.Selection([('pending','Pending'), ('missed','Missed'), ('accepted','Accepted'), ('rejected','Rejected'), ('active','Active'), ('over','Complete')], string='Status', default="pending", help="Pending = Calling person\nActive = currently talking\nMissed = Call timed out\nOver = Someone hit end call\nRejected = Someone didn't want to answer the call")
    start_time = fields.Datetime(string="Answer Time", help="Time the call was answered, create_date is when it started dialing")
    end_time = fields.Datetime(string="End Time", help="Time the call end")
    duration = fields.Char(string="Duration", help="Length of the call")
    transcription = fields.Text(string="Transcription", help="Automatic transcription of the call")
    notes = fields.Text(string="Notes", help="Additional comments outside the transcription")
    client_ids = fields.One2many('voip.call.client', 'vc_id', string="Client List")
    type = fields.Selection([('internal','Internal'),('external','External')], string="Type")
    mode = fields.Selection([('videocall','video call'), ('audiocall','audio call'), ('screensharing','screen sharing call')], string="Mode", help="This is only how the call starts, i.e a video call can turn into a screen sharing call mid way")
    sip_tag = fields.Char(string="SIP Tag")
    direction = fields.Selection([('internal','Internal'), ('incoming','Incoming'), ('outgoing','Outgoing')], string="Direction")

    def accept_call(self):
        """ Mark the call as accepted and send response to close the notification window and open the VOIP window """
        
        if self.status == "pending":
            self.status = "accepted"

        #call_client = request.env['voip.call.client'].search([('vc_id','=', voip_call.id ), ('partner_id','=', request.env.user.partner_id.id) ])
        #call_client.sip_addr_host = request.httprequest.remote_addr
        
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

    def message_bank(self, sdp):

        _logger.error("Message Bank")

        server_sdp = self.env['voip.server'].generate_server_sdp()

        _logger.error(server_sdp)
        
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

    def voip_call_sdp(self, sdp):
        """Store the description and send it to everyone else"""

        _logger.error(sdp)
        
        if self.type == "internal":
            for voip_client in self.client_ids:
                if voip_client.partner_id.id == self.env.user.partner_id.id:
                    voip_client.sdp = sdp
                else:
                    notification = {'call_id': self.id, 'sdp': sdp }
                    self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)
                    
        elif self.type == "external":
            if self.direction == "incoming":
                #Send the 200 OK repsonse with SDP information
                from_client = self.env['voip.call.client'].search([('vc_id', '=', self.id), ('partner_id', '=', self.from_partner_id.id) ])
                to_client = self.env['voip.call.client'].search([('vc_id', '=', self.id), ('partner_id', '=', self.partner_id.id) ])                

                sip_dict = self.env['voip.voip'].sip_read_message(from_client.sip_invite)
                
                _logger.error("From: " + sip_dict['From'].strip().replace(":",">;") )
                _logger.error("To: " + sip_dict['To'].strip().replace(":",">;"))
                _logger.error("CSeq: " + sip_dict['CSeq'].strip())
                _logger.error("Contact: " + sip_dict['Contact'].strip())

                reply = ""
                reply += "SIP/2.0 200 OK\r\n"
                reply += "From: " + from_client.name + "<" + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + to_client.name + "<" + sip_dict['To'].strip() + ";tag=" + str(self.sip_tag) + "\r\n"
                reply += "CSeq: " + sip_dict['CSeq'].strip() + "\r\n"
                reply += "Contact: <sip:" + to_client.name + "@" + to_client.sip_addr_host + ">\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += "Content-Disposition: session\r\n"
                reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                reply += "\r\n"
                reply += sdp_data['sdp'].strip()
                
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(reply, (from_client.sip_addr_host,from_client.sip_addr_port) )

                _logger.error("200 OK: " + reply )


                from_partner_sdp_data = from_client.sip_invite.split("\r\n\r\n")[1]
                from_partner_sdp_data_json = json.dumps({'sdp': from_partner_sdp_data})

                #Send the caller dsp data to the calle now
                for voip_client in self.client_ids:
                    if voip_client.partner_id.id == self.env.user.partner_id.id:
                        notification = {'call_id': self.id, 'sdp': from_partner_sdp_data_json }
                        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)

            elif self.direction == "outgoing":
                #Send the INVITE
                from_sip = self.env.user.partner_id.sip_address.strip()
                to_sip = self.partner_id.sip_address.strip()
                reg_from = from_sip("@")[1]
                reg_to = to_sip.split("@")[1]

                register_string = ""
                register_string += "REGISTER sip:" + reg_to + " SIP/2.0\r\n"
                register_string += "Via: SIP/2.0/UDP " + reg_from + "\r\n"
                register_string += "From: sip:" + from_sip + "\r\n"
                register_string += "To: sip:" + to_sip + "\r\n"
                register_string += "Call-ID: " + "17320@" + reg_to + "\r\n"
                register_string += "CSeq: 1 REGISTER\r\n"
                register_string += "Expires: 7200\r\n"
                register_string += "Contact: " + self.env.user.partner_id.name + "\r\n"

                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(register_string, ('91.121.209.194', 5060) )

                _logger.error("REGISTER: " + register_string)

                #reply = ""
                #reply += "INVITE sip:" + to_sip + " SIP/2.0\r\n"
                #reply += "From: " + request.env.user.partner_id.name + "<sip:" + from_sip + ">; tag = odfgjh\r\n"
                #reply += "To: " + voip_call.partner_id.name.strip + "<sip:" + voip_call.partner_id.sip_address + ">\r\n"
                #reply += "CSeq: 1 INVITE\r\n"
                #reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                #reply += "Content-Type: application/sdp\r\n"
                #reply += "Content-Disposition: session\r\n"
                #reply += "\r\n"
                #reply += sdp_data['sdp']
                
                #serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                #serversocket.sendto(reply, ('91.121.209.194', 5060) )

                #_logger.error("INVITE: " + reply )        

    def voip_call_ice(self, ice):
        """Forward ICE to everyone else"""
        
        #_logger.error("ICE: ")
        #_logger.error(ice)        

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
        
    def rtp_stun_listener(self, d):

        send_data = ""

        if d[1] == "00" and d[2] == "01":
            message_type = "Binding Request"
            
        
        message_length = int( d[3] + d[4], 16)
        message_cookie = d[5] + d[6] + d[7] + d[8]
        transaction_id = d[9] + d[10] + d[11] + d[12] + d[13] + d[14] + d[15] + d[16] + d[17] + d[18] + d[19] + d[20]


        #----Compose binding request-----
        #Message Type (Binding Success Response)
        send_data += "01 01"

        #Message Length (need to calculate)
        send_data += "00 0c"

        #Magic Cookie (always set to 0x2112A442)
        send_data += "21 12 a4 42"

        #96 bit (12 byte) transaction ID (has to be the same as the bind request)
        send_data += transaction_id
        
        #XOR mapped address
        send_data += "00 20"

        #Attribute Length (need to calculate...)
        send_data += "00 08"

        #Reservered (reserved for what...)
        send_data += "00"

        #Protocol Family (Always IPv4 for now...)
        send_data += "01"
        
        #Port (Need to figure this one out...)
        send_data += "f5 43"
        
        #IP XOR-d (Figure this out too...)
        send_data += "a8 81 29 f7"

        #Ok now convert it back so we can send it
        return send_data.replace(" ","").decode('hex')
    
    def rtp_server_listener(self, port, message_bank_duration):
        
        
        #First Message we get is from STUN (Binding Request)
        
        #Second is DTLSv1.2 or more specifically dtls-strp
        
        #3rd is the stream with the G722 Audio payload        
        
        _logger.error("Start RTP Listening on Port " + str(port) )
                        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', port));

        start = time.time()
        stage = "STUN"
        hex_string = ""
        
        #Code is easier to understand if we start at 1 rather then 0...
        hex_data = ['FF']
        
        while time.time() < start + message_bank_duration:
            data, addr = serversocket.recvfrom(2048)

            #Convert to hex so we can human interpret each byte
            for rtp_char in data:
                hex_format = "{0:02x}".format(ord(rtp_char))
                hex_data.append(hex_format)            
                hex_string += hex_format + " "

            #_logger.error("RAW DATA: " + data)
            _logger.error("HEX DATA: " + hex_string)
            
            if stage is "STUN":
                send_data = self.rtp_stun_listener(hex_data)
                _logger.error("SEND DATA: " + send_data)
                serversocket.sendto(send_data, addr )
                
        
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
        #elif mode is "RTCP":
        #    For now we don't use RTCP...
        #    rtc_listener_starter = threading.Thread(target=self.rtcp_server_listener, args=(port,message_bank_duration,))
        #    rtc_listener_starter.start()
 
class VoipCallClient(models.Model):

    _name = "voip.call.client"
    
    vc_id = fields.Many2one('voip.call', string="VOIP Call")
    partner_id = fields.Many2one('res.partner', string="Partner")
    name = fields.Char(string="Name", help="Can be a number if the client is from outside the system")
    state = fields.Selection([('invited','Invited'),('joined','joined'),('media_access','Media Access')], string="State", default="invited")
    sip_invite = fields.Char(string="SIP INVITE Message")
    sip_addr = fields.Char(string="Address")
    sip_addr_host = fields.Char(string="SIP Address Host")
    sip_addr_port = fields.Char(string="SIP Address Port")