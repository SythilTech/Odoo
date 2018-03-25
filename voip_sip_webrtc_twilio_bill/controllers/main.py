# -*- coding: utf-8 -*-
import openerp.http as http
import werkzeug

import logging
_logger = logging.getLogger(__name__)

class TwilioVoiceController(http.Controller):

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