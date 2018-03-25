# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import base64
import odoo
import logging
_logger = logging.getLogger(__name__)

def binary_content(xmlid=None, model='ir.attachment', id=None, field='datas', unique=False, filename=None, filename_field='datas_fname', download=False, mimetype=None, default_mimetype='application/octet-stream', env=None):
    return request.registry['ir.http'].binary_content(
        xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename, filename_field=filename_field,
        download=download, mimetype=mimetype, default_mimetype=default_mimetype, env=env)

class TwilioController(http.Controller):

    @http.route('/sms/twilio/mms/<attachment_id>/<string:filename>', type="http", auth="public", csrf=False)
    def sms_twilio_mms(self, attachment_id, filename):
        """Disable public access to MMS after Twilio has fetched it"""

        attachment = request.env['ir.attachment'].browse( int(attachment_id) )

        if attachment.public == True and attachment.mms == True:

            status, headers, content = binary_content(model='ir.attachment', id=attachment.id, field='datas')

            content_base64 = base64.b64decode(attachment.datas)
            headers.append(('Content-Length', len(content_base64)))

            #Special expection
            _logger.error(attachment.datas_fname)
            if ".mp4" in str(attachment.datas_fname):
                headers.append(('Content-Type', 'video/mp4'))

            response = request.make_response(content_base64, headers)

            #Disable public access since the mms could contain confidential information
            attachment.sudo().write({'public': False})

            return response

        else:
            return "Access Denied"

    @http.route('/sms/twilio/receipt', type="http", auth="public", csrf=False)
    def sms_twilio_receipt(self, **kwargs):
        """Update the state of a sms message, don't trust the posted data"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        request.env['sms.gateway.twilio'].sudo().delivary_receipt(values['AccountSid'], values['MessageSid'])

        return "<Response></Response>"

    @http.route('/sms/twilio/receive', type="http", auth="public", csrf=False)
    def sms_twilio_receive(self, **kwargs):
        """Fetch the new message directly from Twilio, don't trust posted data"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        twilio_account = request.env['sms.account'].sudo().search([('twilio_account_sid','=', values['AccountSid'])])
        request.env['sms.gateway.twilio'].sudo().check_messages(twilio_account.id, values['MessageSid'])

        return "<Response></Response>"