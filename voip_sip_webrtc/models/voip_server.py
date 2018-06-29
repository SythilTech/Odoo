# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
import json
import random
from random import randint
import time
import string
import socket
import datetime
import re

from odoo import api, fields, models, registry
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class VoipVoip(models.Model):

    _name = "voip.server"
    _description = "Voip Server"

    @api.model
    def user_list(self, **kw):
        """ Get all active users so we can place them in the system tray """

        user_list = []

        inactivity_time_minutes = self.env['ir.default'].get('voip.settings', 'inactivity_time')

        #Fail safe because settings are not set to default on module upgrade
        if inactivity_time_minutes is None:
            inactivity_time_minutes == 10

        #This list should only include users that have ever logged in, sort it by last presence that way all the online users are at the top
        for presence_user in self.env['bus.presence'].search([('user_id','!=',self.env.user.id)], order="last_presence desc"):

            #We kinda just assume if a person hasn't been active for 10 minutes they are AFK, this isn't reliable but is better then nothing
            if presence_user.last_presence >= ( datetime.datetime.strptime(presence_user.last_poll, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.timedelta(minutes=inactivity_time_minutes) ).strftime("%Y-%m-%d %H:%M:%S"):
                status = "Online"
            else:
                status = "Offline"

            user_list.append({'name': presence_user.user_id.name, 'partner_id':presence_user.user_id.partner_id.id, 'status': status})        
        
        return user_list

    @api.model
    def sip_call_notify(self, mode, call_type, aor):
        """ Create the VOIP call record and notify the callee of the incoming call """
        
        #Create the VOIP call now so we can mark it as missed / rejected / accepted
        voip_call = self.env['voip.call'].create({'type': call_type, 'mode': mode })
        
        #Find the caller based on the address of record
        from_partner = self.env['res.partner'].search([('sip_address','=', aor)])

        if from_partner == False:
            raise UserError("Could not find SIP partner")
        
        #Add the current user is the call owner
        voip_call.from_partner_id = from_partner.id

        #Add the current user as the to partner
        voip_call.partner_id = self.env.user.partner_id.id

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': from_partner.id, 'state':'joined', 'name': from_partner.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'invited', 'name': self.env.user.partner_id.name})

        #Ringtone will either the default ringtone or the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = self.env['ir.default'].get('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]

        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': from_partner.name, 'caller_partner_id': from_partner.id, 'direction': 'incoming', 'mode':mode, 'sdp': ''}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.env.user.partner_id.id), notification)

    @api.model
    def voip_call_notify(self, mode, to_partner_id, call_type, sdp):
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

        #Ringtone will either the default ringtone or the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = self.env['ir.default'].get('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]

        if voip_call.type == "internal":        
            #Send notification to callee
            notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming', 'mode':mode, 'sdp': sdp}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.partner_id.id), notification)

            #Also send one to yourself so we get the countdown
            notification = {'voip_call_id': voip_call.id, 'ring_duration': ring_duration, 'to_name': voip_call.partner_id.name, 'callee_partner_id': voip_call.partner_id.id, 'direction': 'outgoing'}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', voip_call.from_partner_id.id), notification)
            
        elif voip_call.type == "external":        
            _logger.error("external call")
            
            #Send the INVITE
            voip_account = self.env.user.voip_account_id
            voip_call.voip_account = voip_account
            voip_call.from_partner_sdp = sdp['sdp']
            media_port = random.randint(55000,56000)
            call_id = random.randint(50000,60000)
            from_tag = random.randint(8000000,9000000)

            sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sipsocket.bind(('', 6000))
            bind_port = sipsocket.getsockname()[1]
 
            local_ip = self.env['ir.default'].get('voip.settings', 'server_ip')

            #SDP from webrtc doesn't work?!?
            sdp = sdp['sdp']


            #Server SDP (Works)
            sdp = ""         
            sdp += "v=0\r\n" 
            sess_id = int(time.time())
            sess_version = 0
            sdp += "o=- " + str(sess_id) + " " + str(sess_version) + " IN IP4 " + local_ip + "\r\n"         
            sdp += "s= \r\n"
            sdp += "c=IN IP4 " + local_ip + "\r\n"
            sdp += "t=0 0\r\n"
            sdp += "m=audio " + str(media_port) + " RTP/AVP 0\r\n"      
            sdp += "a=sendrecv\r\n"
            
            #Webrtc SDP Data (Fails)
            sdp = ""
            sdp += "v=0\r\n"
            sdp += "o=mozilla...THIS_IS_SDPARTA-57.0 9175984511205677962 0 IN IP4 0.0.0.0\r\n"
            sdp += "s=-\r\n"
            sdp += "t=0 0\r\n"
            sdp += "a=fingerprint:sha-256 3B:D9:87:A6:7F:E2:B3:F8:0D:92:9F:B7:4A:D7:84:17:E9:C9:5E:70:64:06:85:21:B9:7C:6D:5D:3D:78:36:6B\r\n"
            sdp += "a=group:BUNDLE sdparta_0\r\n"
            sdp += "a=ice-options:trickle\r\n"
            sdp += "a=msid-semantic:WMS *\r\n"
            sdp += "m=audio 9 UDP/TLS/RTP/SAVPF 109 9 0 8 101\r\n"
            sdp += "c=IN IP4 0.0.0.0\r\n"
            sdp += "a=sendrecv\r\n"
            sdp += "a=extmap:1/sendonly urn:ietf:params:rtp-hdrext:ssrc-audio-level\r\n"
            sdp += "a=fmtp:109 maxplaybackrate=48000;stereo=1;useinbandfec=1\r\n"
            sdp += "a=fmtp:101 0-15\r\n"
            sdp += "a=ice-pwd:66f0aeeb56dd05307985a8715f7badcd\r\n"
            sdp += "a=ice-ufrag:afa2841a\r\n"
            sdp += "a=mid:sdparta_0\r\n"
            sdp += "a=msid:{83486b07-4708-46d3-92c7-909f5a598edc} {d04078f0-2166-4d12-b657-c7ca1bb5041b}\r\n"
            sdp += "a=rtcp-mux\r\n"
            sdp += "a=rtpmap:109 opus/48000/2\r\n"
            sdp += "a=rtpmap:9 G722/8000/1\r\n"
            sdp += "a=rtpmap:0 PCMU/8000\r\n"
            sdp += "a=rtpmap:8 PCMA/8000\r\n"
            sdp += "a=rtpmap:101 telephone-event/8000/1\r\n"
            sdp += "a=setup:actpass\r\n"
            sdp += "a=ssrc:645231268 cname:{b132b6ce-4687-4a65-9796-f82caca3ab92}\r\n"
            
            to_address = voip_call.partner_id.mobile.strip()
            
            if "@" not in to_address:
                to_address = to_address + "@" + voip_account.domain
            
            invite_string = ""
            invite_string += "INVITE sip:" + to_address + ":" + str(voip_account.port) + " SIP/2.0\r\n"
            invite_string += "Via: SIP/2.0/UDP " + local_ip + ":" + str(bind_port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
            invite_string += "Max-Forwards: 70\r\n"
            invite_string += "Contact: <sip:" + voip_account.username + "@" + local_ip + ":" + str(bind_port) + ">\r\n"
            invite_string += 'To: <sip:' + to_address + ":" + str(voip_account.port) + ">\r\n"
            invite_string += 'From: "' + voip_account.voip_display_name + '"<sip:' + voip_account.address + ":" + str(voip_account.port) + ">;tag=" + str(from_tag) + "\r\n"
            invite_string += "Call-ID: " + request.env.cr.dbname + "-call-" + str(call_id) + "\r\n"
            invite_string += "CSeq: 1 INVITE\r\n"
            invite_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
            invite_string += "Content-Type: application/sdp\r\n"
            invite_string += "Supported: replaces\r\n"
            invite_string += "User-Agent: Sythil Tech SIP Client\r\n"
            invite_string += "Content-Length: " + str( len(sdp) ) + "\r\n"
            invite_string += "\r\n"
            invite_string += sdp
            
            _logger.error(invite_string )                

            if voip_account.outbound_proxy:
                sipsocket.sendto(invite_string, (voip_account.outbound_proxy, voip_account.port) )
            else:
                sipsocket.sendto(invite_string, (voip_account.domain, voip_account.port) )

            stage = "WAITING"
            while stage == "WAITING":
                sipsocket.settimeout(10)
                data, addr = sipsocket.recvfrom(2048)

                _logger.error(data)

                #Send auth response if challenged
                if data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication Required" or data.split("\r\n")[0] == "SIP/2.0 407 Proxy Authentication required":
                
                    authheader = re.findall(r'Proxy-Authenticate: (.*?)\r\n', data)[0]
                         
                    realm = re.findall(r'realm="(.*?)"', authheader)[0]
                    method = "INVITE"
                    uri = "sip:" + to_address
                    nonce = re.findall(r'nonce="(.*?)"', authheader)[0]
                    qop = re.findall(r'qop="(.*?)"', authheader)[0]
                    nc = "00000001"
                    cnonce = ''.join([random.choice('0123456789abcdef') for x in range(32)])
 
                    #For now we assume qop is present (https://tools.ietf.org/html/rfc2617#section-3.2.2.1)
                    A1 = voip_account.username + ":" + realm + ":" + voip_account.password
                    A2 = method + ":" + uri
                    response = voip_account.KD( voip_account.H(A1), nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + voip_account.H(A2) )

                    reply = ""
                    reply += "INVITE sip:" + to_address + ":" + str(voip_account.port) + " SIP/2.0\r\n"
                    reply += "Via: SIP/2.0/UDP " + local_ip + ":" + str(bind_port) + ";branch=z9hG4bK-524287-1---0d0dce78a0c26252;rport\r\n"
                    reply += "Max-Forwards: 70\r\n"
                    reply += "Contact: <sip:" + voip_account.username + "@" + local_ip + ":" + str(bind_port) + ">\r\n"
                    reply += 'To: <sip:' + to_address + ":" + str(voip_account.port) + ">\r\n"
                    reply += 'From: "' + voip_account.voip_display_name + '"<sip:' + voip_account.address + ":" + str(voip_account.port) + ">;tag=" + str(from_tag) + "\r\n"
                    reply += "Call-ID: " + request.env.cr.dbname + "-call-" + str(call_id) + "\r\n"
                    reply += "CSeq: 1 INVITE\r\n"
                    reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
                    reply += "Content-Type: application/sdp\r\n"
                    reply += 'Proxy-Authorization: Digest username="' + voip_account.username + '",realm="' + realm + '",nonce="' + nonce + '",uri="sip:' + to_address + '",response="' + response + '",cnonce="' + cnonce + '",nc=' + nc + ',qop=auth,algorithm=MD5' + "\r\n"
                    reply += "Supported: replaces\r\n"
                    reply += "User-Agent: Sythil Tech SIP Client\r\n"
                    reply += "Content-Length: " + str( len(sdp) ) + "\r\n"
                    reply += "\r\n"
                    reply += sdp
                    
                    sipsocket.sendto(reply, addr)
                
    @api.model
    def generate_server_ice(self, port, component_id):

        ice_response = ""
        
        #ip_addr = socket.gethostbyname(host)
        ip = self.env['ir.default'].get('voip.settings', 'server_ip')
        
        #See https://tools.ietf.org/html/rfc5245#section-4.1.2.1 (I don't make up these formulas...)
        priority = int((2 ^ 24) * 126) + int((2 ^ 8) * 65535)
        
        #For now we assume the server on has one public facing network card...
        foundation = "0"
        
        ice_response = "candidate:" + foundation + " " + str(component_id) + " UDP " + str(priority) + " " + str(ip) + " " + str(port) + " typ host"
        
        return {"candidate":ice_response,"sdpMid":"sdparta_0","sdpMLineIndex":0}

    @api.model
    def generate_server_sdp(self):
    
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

        #TODO generate before call fingerprint...
        sdp_response += "a=fingerprint:sha-256 DA:52:67:C5:2A:2E:91:13:A2:7D:3A:E1:2E:A4:F3:28:90:67:71:0E:B7:6F:7B:56:79:F4:B2:D1:54:4B:92:7E\r\n"
        #sdp_response += "a=setup:actpass\r\n"
        sdp_response += "a=setup:passive\r\n"
        #sdp_response += "a=setup:active\r\n"
        
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
        ice_ufrag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        ice_pwd = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(22))
        sdp_response += "a=ice-ufrag:" + str(ice_ufrag) + "\r\n"
        sdp_response += "a=ice-pwd:" + str(ice_pwd) + "\r\n"

        #Ummm naming each media?!?
        sdp_response += "a=mid:sdparta_0\r\n"
            
        return {"type":"answer","sdp": sdp_response}