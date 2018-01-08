# -*- coding: utf-8 -*-
import socket
import logging
from openerp.exceptions import UserError
_logger = logging.getLogger(__name__)
from openerp.http import request
import re
import hashlib
import random
from openerp import api, fields, models
import threading
import sdp
import time
import datetime
import struct
import base64
from random import randint
            
class VoipAccountAction(models.Model):

    _name = "voip.account.action"
    _description = "VOIP Account Action"
    _rec_name = "action_type_id"

    account_id = fields.Many2one('voip.account', string="VOIP Account")
    action_type_id = fields.Many2one('voip.account.action.type', string="Call Action", required="True")
    action_type_internal_name = fields.Char(related="action_type_id.internal_name", string="Action Type Internal Name")
    recorded_media_id = fields.Many2one('voip.media', string="Recorded Message")
    user_id = fields.Many2one('res.users', string="Call User")

    def _voip_action_recorded_message(self, session, data):
        _logger.error("Stream recorded message")

        call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
        call_from_full = re.findall(r'From: (.*?)\r\n', data)[0]
        call_from = re.findall(r'<sip:(.*?)>', call_from_full)[0]
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        rtp_ip = re.findall(r'c=IN IP4 (.*?)\r\n', data)[0]
        rtp_audio_port = int(re.findall(r'm=audio (.*?) RTP', data)[0])
        audio_stream = base64.decodestring(self.recorded_media_id.media)
        
        #Create the call now
        voip_call = self.env['voip.call'].create({'from_address': call_from, 'to_address': session.username + "@" + session.domain, 'codec_id': self.recorded_media_id.codec_id.id, 'ring_time': datetime.datetime.now(), 'sip_call_id': call_id })

        #Also create the client list
        voip_call_client = self.env['voip.call.client'].create({'vc_id': voip_call.id, 'audio_media_port': rtp_audio_port, 'sip_address': call_from, 'name': call_from, 'model': False, 'record_id': False})        

        #Answer with a audio call
        audio_media_port = random.randint(55000,56000)            
        call_sdp = sdp.generate_sdp(self, local_ip, audio_media_port, [0])
        session.answer_call(data, call_sdp)
        
        #The call was accepted so start listening for / sending RTP data
        rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rtpsocket.bind(('', voip_call_client.audio_media_port));
        
        rtc_sender_thread = threading.Thread(target=self.account_id.rtp_server_sender, args=(rtpsocket, rtp_ip, rtp_audio_port, audio_stream, voip_call.codec_id, voip_call_client.id,))
        rtc_sender_thread.start()

        rtc_listener_thread = threading.Thread(target=self.account_id.rtp_server_listener, args=(rtc_sender_thread, rtpsocket, voip_call_client.id, voip_call_client.model, voip_call_client.record_id,))
        rtc_listener_thread.start()
            
    def _voip_action_call_user(self, sipsocket, addr, data):
        _logger.error("Call User")        
        
class VoipAccountActionType(models.Model):

    _name = "voip.account.action.type"
    _description = "VOIP Account Action Type"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name", help="function name of code")