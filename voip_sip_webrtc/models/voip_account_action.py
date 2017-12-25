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
            
class VoipAccountAction(models.Model):

    _name = "voip.account.action"
    _description = "VOIP Account Action"
    _rec_name = "action_type_id"

    account_id = fields.Many2one('voip.account', string="VOIP Account")
    action_type_id = fields.Many2one('voip.account.action.type', string="Call Action")
    recorded_media_id = fields.Many2one('voip.media', string="Recorded Message")

    def rtp_server_sender(self, media_port, audio_stream, codec_id, caller_addr, model=False, record_id=False):
        
        try:

            _logger.error("Start RTP Sending From Port " + str(media_port) + " to " + str(caller_addr) )
                
            rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rtpsocket.bind(('', media_port));

            stage = "LISTEN"
            hex_string = ""
            joined_payload = ""

            #Send audio data out every 20ms
            sequence_number = randint(29161, 30000)
            packet_count = 0
            timestamp = (datetime.datetime.utcnow() - datetime.datetime(1900, 1, 1, 0, 0, 0)).total_seconds()
            timestamp = 160
            
            while stage == "LISTEN":

                #---------------------Send Audio Packet-----------
                send_data = self.account_id.generate_rtp_packet(audio_stream, codec_id, packet_count, sequence_number, timestamp)
                rtpsocket.sendto(send_data, caller_addr)
                packet_count += 1
                sequence_number += 1
                timestamp += codec_id.sample_rate / (1000 / codec_id.sample_interval)
                #---------------------END Send Audio Packet-----------
                            
                rtpsocket.settimeout(30)
                data, addr = rtpsocket.recvfrom(2048)
                    
                if packet_count % 100 == 0 or packet_count == 0:
                    _logger.error("GOT RTP DATA")
                    _logger.error(data)
               
                joined_payload += data

        except Exception as e:
            _logger.error(e)

        try:

            #Create the call with the audio
            with api.Environment.manage():
                # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))

                #Start off with the raw audio stream
                create_dict = {'media': joined_payload, 'media_filename': "call.raw", 'codec_id': codec_id.id}
                self.account_id.process_audio_stream( create_dict )

                if model:
                    #Add to the chatter
                    #TODO add SIP subtype
                    self.env[model].browse( int(record_id) ).message_post(body="Call Made", subject="Call Made", message_type="comment")

                #Have to manually commit the new cursor?
                self.env.cr.commit()
        
                self._cr.close()


        except Exception as e:
            _logger.error(e)

    def _voip_action_recorded_message(self, sipsocket, addr, data):
        _logger.error("Stream recorded message")
        
        #Back compatability, moving forward voip.media will be standard for recorded messages
        audio_stream = base64.decodestring(self.recorded_media_id.media)

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

        #Start sending out RTP data now
        caller_addr = (rtp_ip, int(send_media_port) )
        rtc_sender_starter = threading.Thread(target=self.rtp_server_sender, args=(media_port, audio_stream, self.recorded_media_id.codec_id, caller_addr,))
        rtc_sender_starter.start()

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
        #sipsocket.sendto(trying, addr)
        
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
        sdp += "m=audio " + str(media_port) + " RTP/AVP " + str(self.recorded_media_id.codec_id.payload_type) + "\r\n"
                
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
        
class VoipAccountActionType(models.Model):

    _name = "voip.account.action.type"
    _description = "VOIP Account Action Type"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name", help="function name of code")