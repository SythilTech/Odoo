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

from odoo import api, fields, models, registry
from odoo.exceptions import UserError, ValidationError

class VoipVoip(models.Model):

    _name = "voip.server"
    _description = "Voip Server"

    def get_user_agent(self, **kw):
        """ Get SIP adress, auth username and password """

        voip_account = self.env.user.voip_account_id        
        
        if voip_account:
            return {'address': voip_account.address, 'wss': voip_account.wss, 'auth_username': voip_account.auth_username, 'password': voip_account.password}
        else:
            return {'address': ''}        

    def user_list(self, **kw):
        """ Get all active users so we can place them in the system tray """

        user_list = []

        #This list should only include users that have ever logged in, sort it by last presence that way all the online users are at the top
        for presence_user in self.env['bus.presence'].search([('user_id','!=',self.env.user.id)], order="last_presence desc"):

            #We kinda just assume if a person hasn't been active for 5 minutes they are AFK, this isn't reliable but is better then nothing
            if presence_user.last_presence > (datetime.datetime.now() - datetime.timedelta(minutes=5) ).strftime("%Y-%m-%d %H:%M:%S"):
                status = "Online"
            else:
                status = "Offline"

            user_list.append({'name': presence_user.user_id.name, 'partner_id':presence_user.user_id.partner_id.id, 'status': status})        
        
        return user_list

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
        ring_duration = self.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]

        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': from_partner.name, 'caller_partner_id': from_partner.id, 'direction': 'incoming', 'mode':mode, 'sdp': ''}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.env.user.partner_id.id), notification)

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
        ring_duration = self.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
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

            local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

            reply = ""
            reply += "INVITE sip:" + voip_call.partner_id.sip_address.strip() + " SIP/2.0\r\n"
            reply += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
            reply += "Max-Forwards: 70\r\n"
            reply += "Contact: <sip:" + voip_account.username + "@" + local_ip + ":5060>\r\n"
            reply += 'To: <sip:' + voip_call.partner_id.sip_address.strip() + ">\r\n"
            reply += 'From: "' + self.env.user.partner_id.name + '"<sip:' + voip_account.address + ">;tag=903df0a\r\n"
            reply += "Call-ID: " + self.env.cr.dbname + "-call-" + str(voip_call.id) + "\r\n"
            reply += "CSeq: 1 INVITE\r\n"
            reply += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
            reply += "Content-Type: application/sdp\r\n"
            reply += "Supported: replaces\r\n"
            reply += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
            reply += "Content-Length: " + str(len(sdp['sdp'])) + "\r\n"
            reply += "\r\n"
            reply += sdp['sdp']

            _logger.error("INVITE: " + reply )
                
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            serversocket.sendto(reply, (voip_account.outbound_proxy, 5060) )        


            
    @api.model
    def generate_server_ice(self, port, component_id):

        ice_response = ""
        
        #ip_addr = socket.gethostbyname(host)
        ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')
        
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