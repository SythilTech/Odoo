# -*- coding: utf-8 -*-
import openerp.http as http
import werkzeug
from odoo.http import request
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

try:
    from twilio.jwt.client import ClientCapabilityToken
except:
    _logger.error("Twilio Client Not Installed")

class TwilioVoiceController(http.Controller):

    @http.route('/voip/ringtone.mp3', type="http", auth="user")
    def voip_ringtone_mp3(self):
        """Return the ringtone file to be used by javascript"""

        voip_ringtone_id = request.env['ir.default'].get('voip.settings', 'ringtone_id')
        voip_ringtone = request.env['voip.ringtone'].browse( voip_ringtone_id )
        ringtone_media = voip_ringtone.media

        headers = []
        ringtone_base64 = base64.b64decode(ringtone_media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response
        
    @http.route('/twilio/voice', type='http', auth="public", csrf=False)
    def twilio_voice(self, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        from_sip = values['From']
        to_sip = values['To']

        twilio_xml = ""
        twilio_xml += '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
        twilio_xml += "<Response>\n"
        twilio_xml += "  <Dial>\n"
        twilio_xml += "    <Sip>" + to_sip + ";region=gll</Sip>\n"
        twilio_xml += "  </Dial>\n"
        twilio_xml += "</Response>"

        return twilio_xml

    @http.route('/twilio/voice/route', type='http', auth="public", csrf=False)
    def twilio_voice_route(self, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        from_number = values['From']
        to_number = values['To']
        
        to_stored_number = request.env['voip.number'].sudo().search([('number','=',to_number)])

        twilio_xml = ""
        twilio_xml += '<?xml version="1.0" encoding="UTF-8"?>' + "\n"
        twilio_xml += "<Response>\n"
        twilio_xml += '    <Dial callerId="' + from_number + '"'

        setting_record_calls = request.env['ir.default'].get('voip.settings','record_calls')
        
        if setting_record_calls:
            twilio_xml += ' record="record-from-ringing"'
        
        twilio_xml += '>' + "\n"

        
        #Call all the users assigned to this number
        for call_route in to_stored_number.call_routing_ids:
            twilio_xml += "        <Client>" + call_route.twilio_client_name + "</Client>\n"
        
        twilio_xml += "    </Dial>\n"
        twilio_xml += "</Response>"

        return twilio_xml
        
    @http.route('/twilio/capability-token/<stored_number_id>', type='http', auth="public", csrf=False)
    def twilio_capability_token(self, stored_number_id, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        stored_number = request.env['voip.number'].browse( int(stored_number_id) )

        # Find these values at twilio.com/console
        account_sid = stored_number.account_id.twilio_account_sid
        auth_token = stored_number.account_id.twilio_auth_token

        capability = ClientCapabilityToken(account_sid, auth_token)

        # Twilio Application Sid
        application_sid = stored_number.twilio_app_id
        capability.allow_client_outgoing(application_sid)
        capability.allow_client_incoming('the_user_id')
        token = capability.generate()
        
        return {'indentity': 'the_user_id', 'token': token} 