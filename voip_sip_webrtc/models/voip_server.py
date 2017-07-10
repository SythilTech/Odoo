# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json
from random import randint

from odoo import api, fields, models, registry

class VoipVoip(models.Model):

    _name = "voip.server"
    _description = "Voip Server"

    def user_list(self, **kw):
        """ Get all active users so we can place them in the system tray """

        user_list = []
        
        for voip_user in self.env['res.users'].search([('active','=',True), ('share','=', False), ('id', '!=', self.env.user.id)]):
            user_list.append({'name': voip_user.name, 'partner_id':voip_user.partner_id.id})
        
        return user_list

    def voip_call_notify(self, mode, to_partner_id, call_type):
        """ Create the VOIP call record and notify the callee of the incoming call """
        
        #Create the VOIP call now so we can mark it as missed / rejected / accepted
        voip_call = self.env['voip.call'].create({'type': call_type, 'mode': mode })
        
        #Add the current user is the call owner
        voip_call.from_partner_id = self.env.user.partner_id.id

        #Add the selected user as the to partner
        voip_call.partner_id = int(to_partner_id)

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'joined', 'name': self.env.user.partner_id.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': voip_call.partner_id.id, 'state':'invited', 'name': voip_call.partner_id.name})

        #Ringtone will either the default ringtone of the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = self.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]
        
        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming', 'mode':mode}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.partner_id.id), notification)

        #Also send one to yourself so we get the countdown
        notification = {'voip_call_id': voip_call.id, 'ring_duration': ring_duration, 'to_name': voip_call.partner_id.name, 'callee_partner_id': voip_call.partner_id.id, 'direction': 'outgoing'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.from_partner_id.id), notification)

        if voip_call.type == "external":        
            _logger.error("external call")
               
            #Send the REGISTER
            from_sip = voip_call.from_partner_id.sip_address.strip()
            to_sip = voip_call.partner_id.sip_address.strip()
            reg_from = from_sip.split("@")[1]
            reg_to = to_sip.split("@")[1]

            register_string = ""
            register_string += "REGISTER sip:" + reg_to + " SIP/2.0\r\n"
            register_string += "Via: SIP/2.0/UDP " + reg_from + "\r\n"
            register_string += "From: sip:" + from_sip + "\r\n"
            register_string += "To: sip:" + to_sip + "\r\n"
            register_string += "Call-ID: " + "17320@" + reg_to + "\r\n"
            register_string += "CSeq: 1 REGISTER\r\n"
            register_string += "Expires: 7200\r\n"
            register_string += "Contact: " + voip_call.from_partner_id.name + "\r\n"

            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            serversocket.sendto(register_string, ('91.121.209.194', 5060) )

            _logger.error("REGISTER: " + register_string)        

    @api.model
    def generate_server_ice(self, port, component_id):

        ice_response = ""
        ip = "10.0.0.24"
        
        #See https://tools.ietf.org/html/rfc5245#section-4.1.2.1 (I don't make up these formulas...)
        priority = ((2 ^ 24) * 126) + ((2 ^ 8) * 65535)
        
        #For now we assume the server on has one public facing network card...
        foundation = "Sc0a86317"
        
        ice_response = "candidate:" + foundation + " " + str(component_id) + " UDP " + str(priority) + " " + str(ip) + " " + str(port) + " typ host"
        
        return {"candidate":ice_response,"sdpMid":"sdparta_0","sdpMLineIndex":0}

    @api.model
    def generate_server_sdp(self):
    
        sdp_response = ""
                
        #Protocol Version ("v=") https://tools.ietf.org/html/rfc4566#section-5.1 (always 0 for us)
        sdp_response += "v=0\r\n"

        #Origin ("o=") https://tools.ietf.org/html/rfc4566#section-5.2 (should really have a unique sess-id but whatever...)
        sdp_response += "o=- 4835683596547242223 0 IN IP4 0.0.0.0\r\n"
        
        #Session Name ("s=") https://tools.ietf.org/html/rfc4566#section-5.3 (We don't need a session name, information about the call is all displayed in the UI)
        sdp_response += "s= \r\n"
        
        #Timing ("t=") https://tools.ietf.org/html/rfc4566#section-5.9 (For now sessions are infinite but we may use this if for example a company charges a price for a fixed 30 minute consultation)
        sdp_response += "t=0 0\r\n"
        
        #Attributes ("a=") https://tools.ietf.org/html/rfc4566#section-5.13 (standard only mentions some of these...)
        sdp_response += "a=sendrecv\r\n"
        sdp_response += "a=fingerprint:sha-256 77:EF:86:05:29:4F:98:BC:D6:F5:E5:A8:B8:39:DE:5A:C3:90:94:AD:2F:EA:13:DF:FC:EB:9E:87:95:DC:65:C5\r\n"
        sdp_response += "a=ice-options:trickle\r\n"
        sdp_response += "a=msid-semantic:WMS *\r\n"

        #Random stuff, so I don't have get it a second time if needed
        #example supported audio profiles: 109 9 0 8 101
        #sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF 109 101\r\n"
        
        #Use G722 Audio Profile (https://en.wikipedia.org/wiki/RTP_audio_video_profile)
        audio_codec = "9"
        
        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF " + audio_codec + "\r\n"
        
        #Connection Data ("c=") https://tools.ietf.org/html/rfc4566#section-5.7 (always seems to be 0.0.0.0?)
        sdp_response += "c=IN IP4 0.0.0.0\r\n"
        
        #Description of audio 101 / 109 profile?!?
        sdp_response += "a=sendrecv\r\n"
        sdp_response += "a=fmtp:109 maxplaybackrate=48000;stereo=1;useinbandfec=1\r\n"
        sdp_response += "a=fmtp:101 0-15\r\n"
        sdp_response += "a=ice-pwd:c35411c63e8ab7603830d7f4760c6547\r\n"
        sdp_response += "a=ice-ufrag:83315759\r\n"
        sdp_response += "a=mid:sdparta_0\r\n"
        sdp_response += "a=msid:{3778521f-c0cd-47a8-aa20-66c06fbf184e} {7d104cf0-8223-49bf-9ff4-6058cf92e1cf}\r\n"
        sdp_response += "a=rtcp-mux\r\n"
        sdp_response += "a=rtpmap:109 opus/48000/2\r\n"
        sdp_response += "a=rtpmap:101 telephone-event/8000\r\n"
        sdp_response += "a=setup:active\r\n"
        sdp_response += "a=ssrc:615080754 cname:{22894fcb-8532-410d-ad4b-6b8e58e7631a}\r\n"
    
        return {"type":"answer","sdp": sdp_response}
        
    def message_bank(self, voip_call_id, sdp):

        _logger.error("Message Bank")
        voip_call = self.env['voip.call'].browse( int(voip_call_id ) )

        server_sdp = self.env['voip.server'].generate_server_sdp()

        _logger.error(server_sdp)
        
        notification = {'call_id': voip_call.id, 'sdp': server_sdp }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_call.from_partner_id.id), notification)

        #RTP
        port = 62382
        #port = randint(16384,32767)
        server_ice_candidate = self.generate_server_ice(port, 1)        
        self.start_rtc_listener(port, "RTP")
        notification = {'call_id': voip_call.id, 'ice': server_ice_candidate }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_call.from_partner_id.id), notification)

        #RTCP
        port += 1
        server_ice_candidate = self.generate_server_ice(port, 2)
        self.start_rtc_listener(port, "RTCP")
        notification = {'call_id': voip_call.id, 'ice': server_ice_candidate }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_call.from_partner_id.id), notification)

    def rtp_server_listener(self, port):
        _logger.error("Start RTP Listening on Port " + str(port) )
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', port));

        rtc_listening = True
        while rtc_listening:
            data, addr = serversocket.recvfrom(2048)

            _logger.error("RTP: " + data)
            
            if not data: 
                break


    
    def rtcp_server_listener(self, port):
        _logger.error("Start RTCP Listening on Port " + str(port) )
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', port));

        rtc_listening = True
        while rtc_listening:
            data, addr = serversocket.recvfrom(2048)

            _logger.error("RTCP: " + data)
            
            if not data: 
                break



    def start_rtc_listener(self, port, mode):
        #Start a new thread so you don't block the main Odoo thread
        if mode is "RTP":
            rtc_listener_starter = threading.Thread(target=self.rtp_server_listener, args=(port,))
            rtc_listener_starter.start()
        elif mode is "RTCP":
            rtc_listener_starter = threading.Thread(target=self.rtcp_server_listener, args=(port,))
            rtc_listener_starter.start()
