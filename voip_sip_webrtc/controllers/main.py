# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)
import werkzeug.utils
import werkzeug.wrappers
import urllib2
import werkzeug
import base64
import socket
from ast import literal_eval

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class VoipController(http.Controller):         

    @http.route('/voip/user/list', type='json', auth="user")
    def voip_user_list(self, **kw):
        """ Get all active users so we can palcew them in the system tray """

        user_list = []
        
        for voip_user in request.env['res.users'].search([('active','=',True), ('share','=', False), ('id', '!=', request.env.user.id)]):
            user_list.append({'name': voip_user.name, 'partner_id':voip_user.partner_id.id})
        
        return user_list

    @http.route('/voip/call/notify', type="http", auth="user")
    def voip_call_notify(self, mode, to_partner_id, call_type):
        """ STEP 1 Create the VOIP call record and notify the callee of the incoming call """
        
        #We create the voip call record now since we have permission and can track if the call was missed or rejected
        voip_call = request.env['voip.call'].create({'type': call_type, 'mode': mode })
        
        #Add the current user is the call owner
        voip_call.from_partner_id = request.env.user.partner_id.id

        #Add the selected user as the to partner
        voip_call.partner_id = int(to_partner_id)

        #Also add both partners to the client list
        request.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': request.env.user.partner_id.id, 'state':'joined', 'name': request.env.user.partner_id.name})
        request.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': voip_call.partner_id.id, 'state':'invited', 'name': voip_call.partner_id.name})

        #Ringtone will either the default ringtone of the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = request.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(request.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[voip_call.mode]
        
        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': request.env.user.partner_id.name, 'caller_partner_id': request.env.user.partner_id.id, 'direction': 'incoming', 'mode':mode}
        request.env['bus.bus'].sendone((request._cr.dbname, 'voip.notification', voip_call.partner_id.id), notification)

        #Also send one to yourself so we get the countdown
        notification = {'voip_call_id': voip_call.id, 'ring_duration': ring_duration, 'to_name': voip_call.partner_id.name, 'callee_partner_id': voip_call.partner_id.id, 'direction': 'outgoing'}
        request.env['bus.bus'].sendone((request._cr.dbname, 'voip.notification', request.env.user.partner_id.id), notification)

        if voip_call.type == "external":        
            _logger.error("external call")
               
            #Send the REGISTER
            from_sip = request.env.user.partner_id.sip_address.strip()
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
            register_string += "Contact: " + request.env.user.partner_id.name + "\r\n"

            serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            serversocket.sendto(register_string, ('91.121.209.194', 5060) )

            _logger.error("REHISTER: " + register_string)

        
        return "Notify"
        
    @http.route('/voip/ringtone/<voip_call_id>.mp3', type="http", auth="user")
    def voip_ringtone(self, voip_call_id):
        """Return the ringtone file to be used by javascript"""

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        to_user = request.env['res.users'].search([('partner_id','=',voip_call.partner_id.id)])
        
        #Check if the callee has a person ringtone set
        if to_user.voip_ringtone:
            ringtone_media = to_user.voip_ringtone
        else:
            voip_ringtone_id = request.env['ir.values'].get_default('voip.settings', 'ringtone_id')
            voip_ringtone = request.env['voip.ringtone'].browse( voip_ringtone_id )
            ringtone_media = voip_ringtone.media

        headers = []
        ringtone_base64 = base64.b64decode(ringtone_media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response

    @http.route('/voip/messagebank', type="json", auth="user")
    def voip_message_bank(self, voip_call_id, sdp):

        _logger.error("Message Bank")
        voip_call = request.env['voip.call'].browse( int(voip_call_id ) )

        sdp_response = request.env['voip.voip'].generate_server_sdp()
        server_sdp_dict = {"sdp": {"type":"answer","sdp":sdp_response}}
        server_sdp_json = json.dumps(server_sdp_dict)
        
        _logger.error(server_sdp_json)
        notification = {'call_id': voip_call.id, 'sdp': server_sdp_json }
        request.env['bus.bus'].sendone((request._cr.dbname, 'voip.sdp', voip_call.from_partner_id.id), notification)
                    
        return "Message Bank"
                    
    @http.route('/voip/miss/<voip_call_id>.mp3', type="json", auth="user")
    def voip_miss_message(self, voip_call_id):

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        to_user = request.env['res.users'].search([('partner_id','=',voip_call.partner_id.id)])

        if to_user.voip_missed_call:
            missed_call_media = to_user.voip_missed_call

            headers = []
            missed_call_media_base64 = base64.b64decode(missed_call_media)
            headers.append(('Content-Length', len(missed_call_media_base64)))
            response = request.make_response(missed_call_media_base64, headers)
        
            return response
        else:
            return ""


    @http.route('/voip/accept/<call>', type="json", auth="user")
    def voip_accept(self, call):
        """Mark the call as accepted, and open the VOIP window"""
        
        _logger.error(str(call) + " call was accepted")
        voip_call = request.env['voip.call'].browse( int(call) )
        call_client = request.env['voip.call.client'].search([('vc_id','=', voip_call.id ), ('partner_id','=', request.env.user.partner_id.id) ])
        call_client.sip_addr_host = request.httprequest.remote_addr
        voip_call.accept_call()

        return True

    @http.route('/voip/reject/<call>', type="json", auth="user")
    def voip_reject(self, call):
        """Mark the call as rejected"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.reject_call()
                
        return True

    @http.route('/voip/missed/<call>', type="json", auth="user")
    def voip_missed(self, call):
        """Mark the call as missed"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.miss_call()

        return "Bye"

    @http.route('/voip/call/begin', type="http", auth="user")
    def voip_call_begin(self, **kwargs):
        """Remote video was received so this marks the beginning of the call"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
            
        voip_call = request.env['voip.call'].browse( int(values['call']) )
        voip_call.begin_call()
        
        return "hi"


    @http.route('/voip/call/end', type="http", auth="user")
    def voip_call_end(self, **kwargs):
        """Call ends when person clicks the the end call button"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        voip_call.end_call()
                
        return "Bye"
        
    @http.route('/voip/call/sdp', type="http", auth="user")
    def voip_call_sdp(self, **kwargs):
        """Store the description and send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        _logger.error(values['sdp'])
        sdp_json = values['sdp']
        sdp_data = json.loads(sdp_json)['sdp']

        
        if voip_call.type == "internal":
            for voip_client in voip_call.client_ids:
                if voip_client.partner_id.id == request.env.user.partner_id.id:
                    voip_client.sdp = sdp_json
                else:
                    notification = {'call_id': voip_call.id, 'sdp': sdp_json }
                    request.env['bus.bus'].sendone((request._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)
                    
        elif voip_call.type == "external":
            if voip_call.direction == "incoming":
                #Send the 200 OK repsonse with SDP information
                from_client = request.env['voip.call.client'].search([('vc_id', '=', voip_call.id), ('partner_id', '=', voip_call.from_partner_id.id) ])
                to_client = request.env['voip.call.client'].search([('vc_id', '=', voip_call.id), ('partner_id', '=', voip_call.partner_id.id) ])                

                sip_dict = request.env['voip.voip'].sip_read_message(from_client.sip_invite)
                
                _logger.error("From: " + sip_dict['From'].strip().replace(":",">;") )
                _logger.error("To: " + sip_dict['To'].strip().replace(":",">;"))
                _logger.error("CSeq: " + sip_dict['CSeq'].strip())
                _logger.error("Contact: " + sip_dict['Contact'].strip())

                reply = ""
                reply += "SIP/2.0 200 OK\r\n"
                reply += "From: " + from_client.name + "<" + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + to_client.name + "<" + sip_dict['To'].strip() + ";tag=" + str(voip_call.sip_tag) + "\r\n"
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
                for voip_client in voip_call.client_ids:
                    if voip_client.partner_id.id == request.env.user.partner_id.id:
                        notification = {'call_id': voip_call.id, 'sdp': from_partner_sdp_data_json }
                        request.env['bus.bus'].sendone((request._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)

            elif voip_call.direction == "outgoing":
                #Send the INVITE
                from_sip = request.env.user.partner_id.sip_address.strip()
                to_sip = voip_call.partner_id.sip_address.strip()
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
                register_string += "Contact: " + request.env.user.partner_id.name + "\r\n"

                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(register_string, ('91.121.209.194', 5060) )

                _logger.error("REHISTER: " + register_string)

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
        
        return "Hello"

    @http.route('/voip/call/ice', type="http", auth="user")
    def voip_call_ice(self, **kwargs):
        """send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        
        ice_json = values['ice']

        _logger.error("ICE JSON: " + ice_json)
        
        for voip_client in voip_call.client_ids:
            if voip_client.partner_id.id == request.env.user.partner_id.id:
                voip_client.sdp = ice_json

                #ice_candidate = request.env['voip.voip'].generate_server_ice()                
                #notification = {'call_id': voip_call.id, 'ice': json.dumps({"ice":{"candidate":ice_candidate,"sdpMid":"sdparta_0","sdpMLineIndex":0}}) }
                #request.env['bus.bus'].sendone((request._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)                
                
            else:
                notification = {'call_id': voip_call.id, 'ice': ice_json }
                request.env['bus.bus'].sendone((request._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)
        
        return "Hello"
        