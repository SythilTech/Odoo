# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
import base64
import json
import datetime
import time
from email import utils

from openerp import api, fields, models

class VoipCallInheritTWilio(models.Model):

    _inherit = "voip.call"

    twilio_sid = fields.Char(string="Twilio SID")
    twilio_account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    currency_id = fields.Many2one('res.currency', string="Currency")
    price = fields.Float(string="Price")
    margin = fields.Float(string="Margin")
    twilio_number_id = fields.Many2one('voip.number', string="Twilio Number")
    twilio_call_recording = fields.Binary(string="Twilio Call Recording")
    twilio_call_recording_filename = fields.Char(string="Twilio Call Recording Filename")
    record_model = fields.Char(string="Record Model", help="Name of the model this call was to e.g. res.partner / crm.lead")
    record_id = fields.Char(string="Record ID", help="ID of the record the call was to")

    @api.model
    def add_twilio_call(self, voip_call_id, call_sid):
        voip_call = self.env['voip.call'].browse( int(voip_call_id) )
        voip_call.twilio_sid = call_sid

        #Fetch the recording for this call
        twilio_account = voip_call.twilio_account_id
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + twilio_account.twilio_account_sid + "/Calls/" + call_sid + ".json", auth=(str(twilio_account.twilio_account_sid), str(twilio_account.twilio_auth_token)))

        call = json.loads(response_string.text)

        #Fetch the recording if it exists
        if 'subresource_uris' in call:
            if 'recordings' in call['subresource_uris']:
                if call['subresource_uris']['recordings'] != '':
                    recording_response = requests.get("https://api.twilio.com" + call['subresource_uris']['recordings'], auth=(str(twilio_account.twilio_account_sid), str(twilio_account.twilio_auth_token)))
                    recording_json = json.loads(recording_response.text)
                    for recording in recording_json['recordings']:
                        recording_media_uri = "https://api.twilio.com" + recording['uri'].replace(".json",".mp3")
                        recording_media = requests.get(recording_media_uri, auth=(str(twilio_account.twilio_account_sid), str(twilio_account.twilio_auth_token)))
                        voip_call.twilio_call_recording = base64.b64encode(recording_media.content)
                        voip_call.twilio_call_recording_filename = call['sid'] + ".mp3"

        if 'price' in call:
            if float(call['price']) != 0.0:
                voip_call.currency_id = self.env['res.currency'].search([('name','=', call['price_unit'])])[0].id
                voip_call.price = -1.0 * float(call['price'])

        #Have to map the Twilio call status to the one in the core module
        twilio_status = call['status']
        if twilio_status == "queued":
            voip_call.status = "pending"
        elif twilio_status == "ringing":
            voip_call.status = "pending"
        elif twilio_status == "in-progress":
            voip_call.status = "active"
        elif twilio_status == "canceled":
            voip_call.status = "cancelled"
        elif twilio_status == "completed":
            voip_call.status = "over"
        elif twilio_status == "failed":
            voip_call.status = "failed"
        elif twilio_status == "busy":
            voip_call.status = "busy"
        elif twilio_status == "no-answer":
            voip_call.status = "failed"

        voip_call.start_time = datetime.datetime.strptime(call['start_time'], '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')
        voip_call.end_time = datetime.datetime.strptime(call['end_time'], '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')

        #Duration includes the ring time
        voip_call.duration = call['duration']

        #Post to the chatter about the call
        callee = self.env[voip_call.record_model].browse( int(voip_call.record_id) )
        message_body = "A call was made using " + voip_call.twilio_number_id.name + " it lasted " + str(voip_call.duration) + " seconds"
        my_message = callee.message_post(body=message_body, subject="Twilio Outbound Call")