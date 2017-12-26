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
import time
import datetime
import struct
import base64
from random import randint
            
class VoipAccountActionInheritVoice(models.Model):

    _inherit = "voip.account.action"

    voip_voice_message_id = fields.Many2one('voip.voice.message', string="Voice Message")

    def _voip_action_voice_message(self, sipsocket, addr, data):
        _logger.error("Stream voice message")

        #TODO base codec on complex process involving supported RTP profiles from SIP INVITE
        codec_id = self.env['ir.model.data'].sudo().get_object('voip_sip_webrtc', 'pcmu')

        
        bind_port = bind_port = sipsocket.getsockname()[1]
        call_id = re.findall(r'Call-ID: (.*?)\r\n', data)[0]
        call_from = re.findall(r'From: (.*?)\r\n', data)[0]
        call_to = re.findall(r'To: (.*?)\r\n', data)[0]
        from_address = re.findall(r'From: (.*?);', data)[0]
        from_tag = re.findall(r'From: (.*?)\r\n', data)[0].split(";")[0]
        to_tag = random.randint(8000000,9000000)
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')
        media_port = random.randint(55000,56000)
        rtp_ip = re.findall(r'c=IN IP4 (.*?)\r\n', data)[0]
        
        send_media_port = re.findall(r'm=audio (.*?) RTP', data)[0]

        trying = ""
        trying += "SIP/2.0 100 Trying\r\n"
        for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
            trying += "Via: " + via_heading + "\r\n"
        trying += "To: " + call_to + "\r\n"
        trying += "From: " + call_from + "\r\n"
        trying += "Call-ID: " + str(call_id) + "\r\n"
        trying += "CSeq: 1 INVITE\r\n"
        trying += "Content-Length: 0\r\n"
        trying += "\r\n"
        sipsocket.sendto(trying, addr)

        #TODO delay answer the call until the voice synth is complete
        audio_stream = self.voip_voice_message_id.synth_message(codec_id)
        
        #Start sending out RTP data now
        caller_addr = (rtp_ip, int(send_media_port) )
        rtc_sender_starter = threading.Thread(target=self.rtp_server_sender, args=(media_port, audio_stream, codec_id, caller_addr,))
        rtc_sender_starter.start()
        
        ringing = ""
        ringing += "SIP/2.0 180 Ringing\r\n"
        for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
            ringing += "Via: " + via_heading + "\r\n"
        record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
        ringing += "Record-Route: " + record_route + "\r\n"
        ringing += "Contact: <sip:" + self.account_id.username + "@" + local_ip + ":" + str(bind_port) + ";rinstance=a4789de80dfb5716>\r\n"
        ringing += "To: " + call_to + ";tag=" + str(to_tag) + "\r\n"
        ringing += "From: " + call_from + "\r\n"
        ringing += "Call-ID: " + str(call_id) + "\r\n"
        ringing += "CSeq: 1 INVITE\r\n"
        ringing += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        ringing += "Allow-Events: talk, hold\r\n"
        ringing += "Content-Length: 0\r\n"
        ringing += "\r\n"
        #sipsocket.sendto(ringing, addr)

        sdp = ""
        sdp += "v=0\r\n"
        sess_id = int(time.time())
        sdp += "o=- " + str(sess_id) + " 3 IN IP4 " + local_ip + "\r\n"
        sdp += "s= \r\n"
        sdp += "c=IN IP4 " + local_ip + "\r\n"
        sdp += "t=0 0\r\n"
        sdp += "m=audio " + str(media_port) + " RTP/AVP " + str(codec_id.payload_type) + "\r\n"
                
        sdp += "a=sendrecv\r\n"

        #Automated calls are always accepted
        reply = ""
        reply += "SIP/2.0 200 OK\r\n"
        for (via_heading) in re.findall(r'Via: (.*?)\r\n', data):
            reply += "Via: " + via_heading + "\r\n"
        record_route = re.findall(r'Record-Route: (.*?)\r\n', data)[0]
        reply += "Record-Route: " + record_route + "\r\n"
        reply += "Contact: <sip:" + self.account_id.username + "@" + local_ip + ":" + str(bind_port) + ";rinstance=a4789de80dfb5716>\r\n"
        reply += "To: " + call_to + ";tag=" + str(to_tag) + "\r\n"
        reply += "From: " + call_from + "\r\n"
        reply += "Call-ID: " + str(call_id) + "\r\n"
        reply += "CSeq: 1 INVITE\r\n"
        reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        reply += "Content-Type: application/sdp\r\n"
        reply += "Supported: replaces\r\n"
        reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        reply += "Content-Length: " + str(len(sdp)) + "\r\n"
        reply += "\r\n"
        reply += sdp

        sipsocket.sendto(reply, addr)
        