# -*- coding: utf-8 -*-
import werkzeug

import logging
_logger = logging.getLogger(__name__)

class TwilioVoiceController(http.Controller):

    @http.route('/twilio/voice', type='http', auth="public")
    def twilio_voice(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    _logger.error(field_name)
	    _logger.error(field_value)
	    values[field_name] = field_value
	            
	twilio_xml = ""
	
        return twilio_xml