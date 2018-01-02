import requests
import odoo.http as http
import werkzeug
import base64
import json
import ast
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class VoipButtonController(http.Controller):


    @http.route('/voip/website/users', type="json", auth="user", website=True)
    def voip_website_users(self, **kw):

        user_list_html = "<option value=\"\">Select User</option>"

        for call_user in request.env['res.users'].search([]):
            user_list_html += "<option value=\"" + str(call_user.id) + "\">" + call_user.name + "</option>\n"

        return {'user_list_html': user_list_html}


    @http.route('/voip/website/button/add', website=True, type='json', auth="user")
    def voip_website_button_add(self, **kw):
        
        values = {}
        for field_name, field_value in kw.items():
                values[field_name] = field_value

        voip_button = request.env['voip.button'].create({'name': 'New Button', 'url': values['url'], 'user_id': int(values['user_id']) })
        
        return {'voip_button_id': voip_button.id}
        
    @http.route('/voip/button/call/<button_id>', website=True, type='json', auth="public")
    def voip_button_call(self, button_id, **kw):        
        """ Create the VOIP call record and notify the nominated user of the incoming call """

        values = {}
        for field_name, field_value in kw.items():
                values[field_name] = field_value
                
        #Create the VOIP call now so we can mark it as missed / rejected / accepted
        voip_call = request.env['voip.call'].sudo().create({'type': 'internal', 'mode': 'videocall' })
        voip_button = request.env['voip.button'].sudo().browse( int(button_id) )
        
        #Add the voip button user as the callee
        voip_call.partner_id = int(voip_button.user_id.partner_id.id)

        #Also add both partners to the client list
        request.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': voip_call.partner_id.id, 'state':'invited', 'name': voip_call.partner_id.name})

        #Ringtone will either the default ringtone or the users ringtone
        ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
        ring_duration = request.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Send notification to callee
        notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': 'Website User', 'caller_partner_id': False, 'direction': 'incoming', 'mode':'videocall', 'sdp': values['sdp'] }
        request.env['bus.bus'].sendone((request._cr.dbname, 'voip.notification', voip_call.partner_id.id), notification)
               
        return {'voip_call_id': voip_call.id}
        
    @http.route('/voip/button/ice/<call_id>', website=True, type='json', auth="public")
    def voip_button_ice(self, call_id, **kw):        
        """ Share Ice with the callee"""

        values = {}
        for field_name, field_value in kw.items():
                values[field_name] = field_value
                
        _logger.error("Website ICE")
        voip_call = request.env['voip.call'].sudo().browse( int(call_id) )
          
        #Send notification to caller
        notification = {'voip_call_id': voip_call.id] }
        request.env['bus.bus'].sendone('voip.website.sdp' + str(voip_call.id), notification)
        
        notification = {'call_id': voip_call.id, 'ice': values['ice'] }
	request.env['bus.bus'].sendone((request._cr.dbname, 'voip.ice', voip_call.partner_id.id), notification)
