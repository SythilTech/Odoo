# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json

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

    @api.model
    def generate_server_ice(self, port, component_id):

        ice_response = ""
        ip = "10.0.0.24"
        
        #See https://tools.ietf.org/html/rfc5245#section-4.1.2.1 (I don't make up these formulas...)
        priority = ((2 ^ 24) * 126) + ((2 ^ 8) * 65535)
        
        #For now we assume the server on has one public facing network card...
        foundation = "Sc0a86317"
        
        ice_response = "candidate:" + foundation + " " + str(component_id) + " UDP " + str(priority) + " " + str(ip) + " " + str(port) + " typ host"
        
        return ice_response

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
        sdp_response += "a=recvonly\r\n"
        sdp_response += "a=fingerprint:sha-256 77:EF:86:05:29:4F:98:BC:D6:F5:E5:A8:B8:39:DE:5A:C3:90:94:AD:2F:EA:13:DF:FC:EB:9E:87:95:DC:65:C5\r\n"
        sdp_response += "a=ice-options:trickle\r\n"
        sdp_response += "a=msid-semantic:WMS *\r\n"
        
        #Media Descriptions ("m=") https://tools.ietf.org/html/rfc4566#section-5.14 (Message bank is audio only for now)
        sdp_response += "m=audio 9 UDP/TLS/RTP/SAVPF 109 101\r\n"
        
        #Connection Data ("c=") https://tools.ietf.org/html/rfc4566#section-5.7 (always seems to be 0.0.0.0?)
        sdp_response += "c=IN IP4 0.0.0.0\r\n"
        
        #Why is sendrecv appear twice?
        sdp_response += "a=recvonly\r\n"
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
        
        return sdp_response    
        
    def message_bank(self, voip_call_id, sdp):

        _logger.error("Message Bank")
        voip_call = self.env['voip.call'].browse( int(voip_call_id ) )

        sdp_response = self.env['voip.server'].generate_server_sdp()
        server_sdp_dict = {"sdp": {"type":"answer","sdp":sdp_response}}
        server_sdp_json = json.dumps(server_sdp_dict)

        _logger.error(server_sdp_json)
        notification = {'call_id': voip_call.id, 'sdp': server_sdp_json }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sdp', voip_call.from_partner_id.id), notification)

        port = 62382
        ice_candidate_1 = self.generate_server_ice(port, 1)        
        self.start_rtc_listener(port)
        notification = {'call_id': voip_call.id, 'ice': json.dumps({"ice":{"candidate":ice_candidate_1,"sdpMid":"sdparta_0","sdpMLineIndex":0}}) }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_call.from_partner_id.id), notification)

        port += 1
        ice_candidate_2 = self.generate_server_ice(port, 2)        
        self.start_rtc_listener(port)
        notification = {'call_id': voip_call.id, 'ice': json.dumps({"ice":{"candidate":ice_candidate_2,"sdpMid":"sdparta_0","sdpMLineIndex":0}}) }
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.ice', voip_call.from_partner_id.id), notification)

    def rtc_server_listener(self, port):
        _logger.error("Start RTC Listening on Port " + str(port) )
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', port));

        rtc_listening = True
        while rtc_listening:
            data, addr = serversocket.recvfrom(2048)

            _logger.error(data)
            
            if not data: 
                break

            _logger.error(data)

    def start_rtc_listener(self, port):
        #Start a new thread so you don't block the main Odoo thread
        rtc_listener_starter = threading.Thread(target=self.rtc_server_listener, args=(port,))
        rtc_listener_starter.start()
