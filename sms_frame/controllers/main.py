# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import base64
import odoo
import requests
import logging
_logger = logging.getLogger(__name__)
from lxml import etree
from datetime import datetime

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
        """Read the message and extract the media attachment if present"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        account_id = request.env['sms.account'].sudo().search([('twilio_account_sid','=', values['AccountSid'])])[0]

        delivary_state = ""
        if values['SmsStatus'] == "failed":
            delivary_state = "failed"
        elif values['SmsStatus'] == "sent":
            delivary_state = "successful"
        elif values['SmsStatus'] == "delivered":
            delivary_state = "DELIVRD"
        elif values['SmsStatus'] == "undelivered":
            delivary_state = "UNDELIV"
        elif values['SmsStatus'] == "received":
            delivary_state = "RECEIVED"

        my_message = request.env['sms.message'].sudo().search([('sms_gateway_message_id','=', values['MessageSid'] )])
        if len(my_message) == 0:

            #Have to convert it into XML because the underlying function expects it and I'm too lazy to revamp this whole module to use json...
            root = etree.fromstring("<Message><From>" + values['From'] + "</From></Message>")
            my_messages = root.xpath('//Message')
            sms_message = my_messages[0]
            target = request.env['sms.message'].sudo().find_owner_model(sms_message)

            twilio_gateway_id = request.env['sms.gateway'].sudo().search([('gateway_model_name', '=', 'sms.gateway.twilio')])

            discussion_subtype = request.env['ir.model.data'].sudo().get_object('mail', 'mt_comment')
            my_message = ""

            attachments = []

            if int(values['NumMedia']) > 0:
                sms_account = request.env['sms.account'].sudo().browse(account_id)
                media_filename = values['MessageSid'] + ".jpg"
                attachments.append((media_filename, requests.get(values['MediaUrl0']).content) )

            from_record = request.env['res.partner'].sudo().search([('mobile','=', values['From'])])

            if from_record:
                message_subject = "SMS Received from " + from_record.name
            else:
                message_subject = "SMS Received from " + values['From']

            if target['target_model'] == "res.partner":
                model_id = request.env['ir.model'].sudo().search([('model','=', target['target_model'])])

                my_record = request.env[target['target_model']].sudo().browse( int(target['record_id'].id) )
                my_message = my_record.message_post(body=values['Body'], subject=message_subject, subtype_id=discussion_subtype.id, author_id=my_record.id, message_type="comment", attachments=attachments)
                _logger.error(my_message.id)

                #Notify followers of this partner who are listenings to the 'discussions' subtype
                for notify_partner in request.env['mail.followers'].sudo().search([('res_model','=','res.partner'),('res_id','=',target['record_id'].id), ('subtype_ids','=',discussion_subtype.id)]):
                    my_message.needaction_partner_ids = [(4,notify_partner.partner_id.id)]

                #Create the sms record in history
                history_id = request.env['sms.message'].sudo().create({'account_id': account_id.id, 'status_code': "RECEIVED", 'from_mobile': values['From'], 'to_mobile': values['To'], 'sms_gateway_message_id': values['MessageSid'], 'sms_content': values['Body'], 'direction':'I', 'message_date':datetime.now(), 'model_id':model_id.id, 'record_id':int(target['record_id'].id), 'by_partner_id': my_record.id})
            elif target['target_model'] == "crm.lead":
                model_id = request.env['ir.model'].sudo().search([('model','=', target['target_model'])])

                my_record = request.env[target['target_model']].sudo().browse( int(target['record_id'].id) )
                my_message = my_record.message_post(body=values['Body'], subject=message_subject, subtype_id=discussion_subtype.id, message_type="comment", attachments=attachments)

                #Notify followers of this lead who are listenings to the 'discussions' subtype
                for notify_partner in request.env['mail.followers'].sudo().search([('res_model','=','crm.lead'),('res_id','=',target['record_id'].id), ('subtype_ids','=',discussion_subtype.id)]):
                    my_message.needaction_partner_ids = [(4,notify_partner.partner_id.id)]

                #Create the sms record in history
                history_id = request.env['sms.message'].sudo().create({'account_id': account_id.id, 'status_code': "RECEIVED", 'from_mobile': values['From'], 'to_mobile': values['To'], 'sms_gateway_message_id': values['MessageSid'], 'sms_content': values['Body'], 'direction':'I', 'message_date':datetime.now(), 'model_id':model_id.id, 'record_id':int(target['record_id'].id)})
            else:
                #Create the sms record in history without the model or record_id 
                history_id = request.env['sms.message'].sudo().create({'account_id': account_id.id, 'status_code': "RECEIVED", 'from_mobile': values['From'], 'to_mobile': values['To'], 'sms_gateway_message_id': values['MessageSid'], 'sms_content': values['Body'], 'direction':'I', 'message_date':datetime.now()})

        return "<Response></Response>"