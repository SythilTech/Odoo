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
   
    @http.route('/voip/ringtone/<ringtone>/<filename>', type="http", auth="user")
    def voip_ringtone(self, ringtone, filename):
        """Return the ringtone file to be used by javascript"""
        
        voip_ringtone = request.env['voip.ringtone'].browse( int(ringtone) )

        headers = []
        ringtone_base64 = base64.b64decode(voip_ringtone.media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response

    @http.route('/voip/accept/<call>', type="json", auth="user")
    def voip_accept(self, call):
        """Mark the call as accepted, and open the VOIP window"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        #voip_call.start_time = datetime.datetime.now()
        
        #Assign yourself as the to partner
        voip_call.partner_id = request.env.user.partner_id.id
        
        #Notify caller and callee that the call was accepted
        for voip_client in voip_call.client_ids:
            notification = {'call_id': voip_call.id, 'status': 'accepted', 'type': voip_call.type}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)

        return True

    @http.route('/voip/reject/<call>', type="json", auth="user")
    def voip_reject(self, call):
        """Mark the call as rejected"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        
        if voip_call.status == "pending":
            voip_call.status = "rejected"
        
        #Notify caller and callee that the call was rejected
        for voip_client in voip_call.client_ids:
            notification = {'call_id': voip_call.id, 'status': 'rejected'}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.response', voip_client.partner_id.id), notification)
        
        return True

    @http.route('/voip/missed/<call>', type="json", auth="user")
    def voip_missed(self, call):
        """Mark the call as missed"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.status = "missed"
        return True
            
    @http.route('/voip/window', type="http", auth="user")
    def voip_window(self, **kwargs):
        """Window for video calls which can be dragged around"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        voip_call = request.env['voip.call'].browse( int(values['call']) )

        request.uid = request.session.uid
        context = request.env['ir.http'].webclient_rendering_context()

        context['voip_call'] = voip_call
        
        return http.request.render('voip_sip_webrtc.voip_window', qcontext=context)

    @http.route('/voip/call/connect', type="http", auth="user")
    def voip_call_connect(self, **kwargs):
        """The user has accepted camera / audio access, notify everyone else in the call room"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
            
        voip_call = request.env['voip.call'].browse( int(values['call']) )

        voip_client = request.env['voip.call.client'].sudo().search([('vc_id','=', voip_call.id), ('partner_id', '=', request.env.user.partner_id.id) ])[0]
        
        #The client has accepted media access
        voip_client.state = "media_access"


        #If both clients have accepted media access we start the call
        if request.env['voip.call.client'].sudo().search_count([('vc_id','=', voip_call.id), ('state', '=', "media_access") ]) == 2:        
            
            #Send a notification to the caller to signal the start of the call
            notification = {'call_id': voip_call.id}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.start', request.env.user.partner_id.id), notification)

        return "hi"

    @http.route('/voip/call/begin', type="http", auth="user")
    def voip_call_begin(self, **kwargs):
        """Remote video was received so this marks the beginning of the call"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
            
        voip_call = request.env['voip.call'].browse( int(values['call']) )
        voip_call.start_time = datetime.datetime.now() 
        
        return "hi"

    @http.route('/voip/call/sdp', type="http", auth="user")
    def voip_call_sdp(self, **kwargs):
        """Store the description and send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        
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
                sip_dict = request.env['voip.voip'].sip_read_message(from_client.sip_invite)
                reply = ""
                reply += "SIP/2.0 200 OK\r\n"
                reply += "From: " + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + sip_dict['To'].strip() + ";tag=" + str(voip_call.sip_tag) + "\r\n"
                reply += "CSeq: " + sip_dict['CSeq'].strip() + "\r\n"
                reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += "Content-Disposition: session\r\n"
                reply += "\r\n"
                reply += sdp_data['sdp']
                
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(reply, literal_eval(from_client.sip_addr) )

                _logger.error("200 OK: " + reply )
            elif voip_call.direction == "outgoing":
                #Send the INVITE
                from_sip = request.env.user.partner_id.sip_address.strip()
                to_sip = voip_call.partner_id.sip_address.strip()
                reply = ""
                reply += "INVITE sip:" + to_sip + " SIP/2.0\r\n"
                reply += "From: " + request.env.user.partner_id.name + "<sip:" + from_sip + ">; tag = odfgjh\r\n"
                reply += "To: " + voip_call.partner_id.name.strip + "<sip:" + voip_call.partner_id.sip_address + ">\r\n"
                reply += "CSeq: 1 INVITE\r\n"
                reply += "Content-Length: " + str( len( sdp_data['sdp'] ) ) + "\r\n"
                reply += "Content-Type: application/sdp\r\n"
                reply += "Content-Disposition: session\r\n"
                reply += "\r\n"
                reply += sdp_data['sdp']
                
                serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                serversocket.sendto(reply, ('91.121.209.194', 5060) )

                _logger.error("INVITE: " + reply )
        
        return "Hello"

    @http.route('/voip/call/ice', type="http", auth="user")
    def voip_call_ice(self, **kwargs):
        """send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        
        ice_json = values['ice']
        
        for voip_client in voip_call.client_ids:
            if voip_client.partner_id.id == request.env.user.partner_id.id:
                voip_client.sdp = ice_json
            else:
                notification = {'call_id': voip_call.id, 'ice': ice_json }
                request.env['bus.bus'].sendone((request._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)
        
        return "Hello"
        
    @http.route('/voip/call/end', type="http", auth="user")
    def voip_call_end(self, **kwargs):
        """Call ends when person clicks the the end call button"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call']) )
        voip_call.status = 'over'
        voip_call.end_time = datetime.datetime.now()
        diff_time = datetime.datetime.strptime(voip_call.end_time, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(voip_call.start_time, DEFAULT_SERVER_DATETIME_FORMAT)
        voip_call.duration = str(diff_time.seconds) + " Seconds"

        #Notify both caller and callee that the call is ended
        for voip_client in voip_call.client_ids:
            notification = {'call_id': voip_call.id}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.end', voip_client.partner_id.id), notification)
        
        return "Bye"