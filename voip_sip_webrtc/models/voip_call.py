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
#import ssl
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
    call_dialog_id = fields.Many2one('voip.codec', string="Call Dialog")

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
        fignerprint = self.env['ir.default'].get('voip.settings', 'fingerprint')
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
                    
    def voip_call_ice(self, ice):
        """Forward ICE to everyone else"""
        
        for voip_client in self.client_ids:
            
            #Don't send ICE back to yourself
            if voip_client.partner_id.id != self.env.user.partner_id.id:
                notification = {'call_id': self.id, 'ice': ice }
                self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)
 
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