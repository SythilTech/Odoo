# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

from openerp.http import request
from openerp import api, fields, models
from openerp.exceptions import UserError

class sms_response():
     delivary_state = ""
     response_string = ""
     human_read_error = ""
     mms_url = ""
     message_id = ""

class SmsGatewayTwilio(models.Model):

    _name = "sms.gateway.twilio"
    _description = "Twilio SMS Gateway"

    api_url = fields.Char(string='API URL')

    def send_message(self, sms_gateway_id, from_number, to_number, sms_content, my_model_name='', my_record_id=0, media=None, queued_sms_message=None, media_filename=False):
        """Actual Sending of the sms"""
        sms_account = self.env['sms.account'].search([('id','=',sms_gateway_id)])

        #format the from number before sending
        format_from = from_number
        if " " in format_from: format_from.replace(" ", "")

        #format the to number before sending
        format_to = to_number
        if " " in format_to: format_to.replace(" ", "")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        media_url = ""
        #Create an attachment for the mms now since we need a url now
        if media:

            attachment_id = self.env['ir.attachment'].sudo().create({'name': 'mms ' + str(my_record_id), 'type': 'binary', 'datas': media, 'public': True, 'mms': True, 'datas_fname': media_filename})

            #Force the creation of the new attachment before you make the request
            request.env.cr.commit()

            if media_filename:
                media_url = base_url + "/sms/twilio/mms/" + str(attachment_id.id) + "/" + media_filename
            else:
                media_url = base_url + "/sms/twilio/mms/" + str(attachment_id.id) + "/media." + attachment_id.mimetype.split("/")[1]


        #send the sms/mms
        payload = {'From': format_from, 'To': format_to, 'Body': sms_content, 'StatusCallback': base_url + "/sms/twilio/receipt"}

        if queued_sms_message:
            for mms_attachment in queued_sms_message.attachment_ids:
                #For now we only support a single MMS per message but that will change in future versions
                payload['MediaUrl'] = base_url + "/web/image/" + str(mms_attachment.id) + "/media." + mms_attachment.mimetype.split("/")[1]            

        if media:
            payload['MediaUrl'] = media_url

        response_string = requests.post("https://api.twilio.com/2010-04-01/Accounts/" + str(sms_account.twilio_account_sid) + "/Messages", data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))

        #Analyse the reponse string and determine if it sent successfully other wise return a human readable error message   
        human_read_error = ""
        root = etree.fromstring(response_string.text.encode("utf-8"))
        my_elements_human = root.xpath('/TwilioResponse/RestException/Message')
        if len(my_elements_human) != 0:
            human_read_error = my_elements_human[0].text

        #The message id is important for delivary reports also set delivary_state=successful
        sms_gateway_message_id = ""
        delivary_state = "failed"
        my_elements = root.xpath('//Sid')
        if len(my_elements) != 0:
            sms_gateway_message_id = my_elements[0].text
            delivary_state = "successful"

        #send a repsonse back saying how the sending went
        my_sms_response = sms_response()
        my_sms_response.delivary_state = delivary_state
        my_sms_response.response_string = response_string.text
        my_sms_response.human_read_error = human_read_error
        my_sms_response.message_id = sms_gateway_message_id
        return my_sms_response

    def check_messages(self, account_id, message_id=""):
        """Checks for any new messages or if the message id is specified get only that message"""
        sms_account = self.env['sms.account'].browse(account_id)

        if message_id != "":
            payload = {}
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + sms_account.twilio_account_sid + "/Messages/" + message_id, data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
            twil_xml = response_string.text.encode('utf-8')
            parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
            root = etree.fromstring(twil_xml, parser=parser)
            my_messages = root.xpath('//Message')
            sms_message = my_messages[0]
            #only get the inbound ones as we track the outbound ones back to a user profile
            if sms_message.xpath('//Direction')[0].text == "inbound":
                self._add_message(sms_message, account_id)
        else:
            #get a list of all new inbound message since the last check date
            payload = {}
            if sms_account.twilio_last_check_date != False:
                my_time = datetime.strptime(sms_account.twilio_last_check_date,'%Y-%m-%d %H:%M:%S')
                payload = {'DateSent>': str(my_time.strftime('%Y-%m-%d'))}
            response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + sms_account.twilio_account_sid + "/Messages", data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
            root = etree.fromstring(response_string.text.encode("utf-8"))

            #get all pages
            messages_tag = root.xpath('//Messages')

            #Loop through all pages until you have reached the end
            while True:

                my_messages = messages_tag[0].xpath('//Message')
                for sms_message in my_messages:

                    #only get the inbound ones as we track the outbound ones back to a user profile
                    if sms_message.find('Direction').text == "inbound":
                        self._add_message(sms_message, account_id)

                #get the next page if there is one
                next_page_uri = messages_tag[0].attrib['nextpageuri']
                if next_page_uri != "":
                    response_string = requests.get("https://api.twilio.com" + messages_tag[0].attrib['nextpageuri'], data=payload, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))
                    root = etree.fromstring(response_string.text.encode("utf-8"))
                    messages_tag = root.xpath('//Messages')

                #End the loop if there are no more pages
                if next_page_uri == "":
                    break

        sms_account.twilio_last_check_date = datetime.utcnow()

    def _add_message(self, sms_message, account_id):
        """Adds the new sms to the system"""       
        delivary_state = ""
        if sms_message.find('Status').text == "failed":
            delivary_state = "failed"
        elif sms_message.find('Status').text == "sent":
            delivary_state = "successful"
        elif sms_message.find('Status').text == "delivered":
            delivary_state = "DELIVRD"
        elif sms_message.find('Status').text == "undelivered":
            delivary_state = "UNDELIV"
        elif sms_message.find('Status').text == "received":
            delivary_state = "RECEIVED"

        my_message = self.env['sms.message'].search([('sms_gateway_message_id','=', sms_message.find('Sid').text)])
        if len(my_message) == 0 and sms_message.find('Direction').text == "inbound":

            target = self.env['sms.message'].find_owner_model(sms_message)

            twilio_gateway_id = self.env['sms.gateway'].search([('gateway_model_name', '=', 'sms.gateway.twilio')])

            discussion_subtype = self.env['ir.model.data'].get_object('mail', 'mt_comment')
            my_message = ""

            attachments = []

            _logger.error(sms_message.find('NumMedia').text)
            if int(sms_message.find('NumMedia').text) > 0:
                sms_account = self.env['sms.account'].browse(account_id)

                for sub_resource in sms_message.find('SubresourceUris'):
                    media_list_url = sub_resource.text
                    _logger.error(media_list_url)

                    media_response_string = requests.get("https://api.twilio.com" + media_list_url, auth=(str(sms_account.twilio_account_sid), str(sms_account.twilio_auth_token)))

                    media_root = etree.fromstring(media_response_string.text.encode("utf-8"))
                    for media_mms in media_root.xpath('//MediaList/Media'):
                        first_media_url = media_mms.find('Uri').text
                        media_filename = media_mms.find("Sid").text + ".jpg"
                        attachments.append((media_filename, requests.get("https://api.twilio.com" + first_media_url).content) )

            from_record = self.env['res.partner'].sudo().search([('mobile','=', sms_message.find('From').text)])

            if from_record:
                message_subject = "SMS Received from " + from_record.name
            else:
                message_subject = "SMS Received from " + sms_message.find('From').text

            if target['target_model'] == "res.partner":
                model_id = self.env['ir.model'].search([('model','=', target['target_model'])])

                my_record = self.env[target['target_model']].browse( int(target['record_id'].id) )
                my_message = my_record.message_post(body=sms_message.find('Body').text, subject=message_subject, subtype_id=discussion_subtype.id, author_id=my_record.id, message_type="comment", attachments=attachments)

                #Notify followers of this partner who are listenings to the 'discussions' subtype
                for notify_partner in self.env['mail.followers'].search([('res_model','=','res.partner'),('res_id','=',target['record_id'].id), ('subtype_ids','=',discussion_subtype.id)]):
                    my_message.needaction_partner_ids = [(4,notify_partner.partner_id.id)]

                #Create the sms record in history
                history_id = self.env['sms.message'].create({'account_id': account_id, 'status_code': "RECEIVED", 'from_mobile': sms_message.find('From').text, 'to_mobile': sms_message.find('To').text, 'sms_gateway_message_id': sms_message.find('Sid').text, 'sms_content': sms_message.find('Body').text, 'direction':'I', 'message_date':sms_message.find('DateUpdated').text, 'model_id':model_id.id, 'record_id':int(target['record_id'].id), 'by_partner_id': my_record.id})
            elif target['target_model'] == "crm.lead":
                model_id = self.env['ir.model'].search([('model','=', target['target_model'])])

                my_record = self.env[target['target_model']].browse( int(target['record_id'].id) )
                my_message = my_record.message_post(body=sms_message.find('Body').text, subject=message_subject, subtype_id=discussion_subtype.id, message_type="comment", attachments=attachments)

                #Notify followers of this lead who are listenings to the 'discussions' subtype
                for notify_partner in self.env['mail.followers'].search([('res_model','=','crm.lead'),('res_id','=',target['record_id'].id), ('subtype_ids','=',discussion_subtype.id)]):
                    my_message.needaction_partner_ids = [(4,notify_partner.partner_id.id)]

                #Create the sms record in history
                history_id = self.env['sms.message'].create({'account_id': account_id, 'status_code': "RECEIVED", 'from_mobile': sms_message.find('From').text, 'to_mobile': sms_message.find('To').text, 'sms_gateway_message_id': sms_message.find('Sid').text, 'sms_content': sms_message.find('Body').text, 'direction':'I', 'message_date':sms_message.find('DateUpdated').text, 'model_id':model_id.id, 'record_id':int(target['record_id'].id)})
            else:
                #Create the sms record in history without the model or record_id 
                history_id = self.env['sms.message'].create({'account_id': account_id, 'status_code': "RECEIVED", 'from_mobile': sms_message.find('From').text, 'to_mobile': sms_message.find('To').text, 'sms_gateway_message_id': sms_message.find('Sid').text, 'sms_content': sms_message.find('Body').text, 'direction':'I', 'message_date':sms_message.find('DateUpdated').text})

    def delivary_receipt(self, account_sid, message_id):
        """Updates the sms message when it is successfully received by the mobile phone"""
        my_account = self.env['sms.account'].search([('twilio_account_sid','=', account_sid)])[0]
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + my_account.twilio_account_sid + "/Messages/" + message_id, auth=(str(my_account.twilio_account_sid), str(my_account.twilio_auth_token)))
        root = etree.fromstring(str(response_string.text))

        #map the Twilio delivary code to the sms delivary states 
        delivary_state = ""
        if root.xpath('//Status')[0].text == "failed":
            delivary_state = "failed"
        elif root.xpath('//Status')[0].text == "sent":
            delivary_state = "successful"
        elif root.xpath('//Status')[0].text == "delivered":
            delivary_state = "DELIVRD"
        elif root.xpath('//Status')[0].text == "undelivered":
            delivary_state = "UNDELIV"

        my_message = self.env['sms.message'].search([('sms_gateway_message_id','=', message_id)])
        if len(my_message) > 0:
            my_message[0].status_code = delivary_state
            my_message[0].delivary_error_string = root.xpath('//ErrorMessage')[0].text

class SmsAccountTwilio(models.Model):

    _inherit = "sms.account"
    _description = "Adds the Twilio specfic gateway settings to the sms gateway accounts"

    twilio_account_sid = fields.Char(string='Account SID')
    twilio_auth_token = fields.Char(string='Auth Token')
    twilio_last_check_date = fields.Datetime(string="Last Check Date")

    @api.one
    def twilio_quick_setup(self):
        """Configures your Twilio account so inbound messages point to your server, also adds mobile numbers to the system"""
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))
        if response_string.status_code == 200:
            response_string_twilio_numbers = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/IncomingPhoneNumbers", auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))

            #go through each twilio number in the account and set the the sms url
            root = etree.fromstring(response_string_twilio_numbers.text.encode("utf-8"))
            my_from_number_list = root.xpath('//IncomingPhoneNumber')
            for my_from_number in my_from_number_list:
                av_phone = my_from_number.xpath('//PhoneNumber')[0].text
                sid = my_from_number.xpath('//Sid')[0].text

                #Create a new mobile number
                if self.env['sms.number'].search_count([('mobile_number','=',av_phone)]) == 0:
                    vsms = self.env['sms.number'].create({'name': av_phone, 'mobile_number': av_phone,'account_id':self.id})

                payload = {'SmsUrl': str(request.httprequest.host_url + "sms/twilio/receive")}
                requests.post("https://api.twilio.com/2010-04-01/Accounts/" + self.twilio_account_sid + "/IncomingPhoneNumbers/" + sid, data=payload, auth=(str(self.twilio_account_sid), str(self.twilio_auth_token)))

                #Check for new messages
                self.env['sms.gateway.twilio'].check_messages(self.id)
        else:
            UserError("Bad Credentials")