# -*- coding: utf-8 -*-
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, registry

class VoipVoip(models.Model):

    _name = "voip.voip"
    _description = "Voip Functions"

    @api.model
    def sip_read_message(self, data):
        sip_dict = {}
        for line in data.split("\n"):
            sip_key = line.split(":")[0]
            sip_value = line[len(sip_key) + 2:]
            sip_dict[sip_key] = sip_value

        #Get from SIP address
        from_sip = sip_dict['From']
        start = from_sip.index( "sip:" ) + 4
        end = from_sip.index( ";", start )
        sip_dict['from_sip'] = from_sip[start:end].replace(">","").strip()

        #Get to SIP address
        sip_dict['to_sip'] = sip_dict['To'].split("sip:")[1].strip()
            
        return sip_dict

    @api.model
    def generate_server_ice(self):

        ice_response = ""
        ip = "10.0.0.29"
        port = "62380"
        
        #See https://tools.ietf.org/html/rfc5245#section-4.1.2.1 (I don't make up these formulas...)
        priority = ((2 ^ 24) * 126) + ((2 ^ 8) * 65535)
        
        ice_response = "candidate:0 1 UDP " + str(priority) + " " + str(ip) + " " + str(port) + " typ host"
        
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

    @api.model
    def start_sip_call(self, to_partner):
        #Ask for media permission from the caller
        mode = "audiocall"
        constraints = {'audio': True}
        notification = {'mode': mode, 'to_partner_id': to_partner, 'constraints':  constraints, 'call_type': 'external'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.permission', self.env.user.partner_id.id), notification)
                    
    @api.model
    def start_incoming_sip_call(self, sip_invite, addr, sip_tag):

        sip_dict = self.sip_read_message(sip_invite)

        #Find the from partner
        from_partner_id = self.env['res.partner'].sudo().search([('sip_address', '=', sip_dict['from_sip'] )])

        #Find the to partner
        to_partner_id = self.env['res.partner'].sudo().search([('sip_address', '=', sip_dict['to_sip'] )])
            
        #SIP INVITE will continously send, only allow one call from this person at a time, as a future feature if multiple people call they are allowed to join the call with permission
        if self.env['voip.call'].search_count([('status', '=', 'pending'), ('from_partner_id', '=', from_partner_id.id), ('partner_id', '=', to_partner_id.id)]) < 50:

            _logger.error("INVITE: " + str(sip_invite) )
            _logger.error("from partner:" + str(from_partner_id.name) )
            _logger.error("to partner:" + str(to_partner_id.name) )
            
            #The call is created now so we can update it as a missed / rejected call or accepted, the timer for the call starts after being accepted though
            voip_call = self.env['voip.call'].create({'type': 'external', 'direction': 'incoming', 'sip_tag': sip_tag})

            ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
            ring_duration = self.env['ir.values'].get_default('voip.settings', 'ring_duration')
            
            #Assign the caller and callee partner
            voip_call.from_partner_id = from_partner_id
            voip_call.partner_id = to_partner_id

            #Add the to calle to the client list
            self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': to_partner_id.id, 'state':'joined', 'name': to_partner_id.name})

            #Also add the external partner to the list but assume we already have media access, the long polling will be ignored since the from is external to the system
            self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': from_partner_id.id, 'state':'media_access', 'name': from_partner_id.name, 'sip_invite': sip_invite, 'sip_addr_host': addr[0], 'sip_addr_port': addr[1] })

            #Send notification to callee
            notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': from_partner_id.name, 'caller_partner_id': from_partner_id.id, 'direction': 'incoming', 'mode': "audiocall"}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', to_partner_id.id), notification)
        
        #Have to manually commit the new cursor?
        self.env.cr.commit()