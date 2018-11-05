# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
import base64
import json
import datetime
import time
from email import utils
from openerp.http import request

from openerp import api, fields, models

class VoipCallInheritTWilio(models.Model):

    _inherit = "voip.call"

    twilio_sid = fields.Char(string="Twilio SID")
    twilio_account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    currency_id = fields.Many2one('res.currency', string="Currency")
    price = fields.Float(string="Price")
    margin = fields.Float(string="Margin")
    twilio_number_id = fields.Many2one('voip.number', string="Twilio Number")
    twilio_call_recording_uri = fields.Char(string="Twilio Call Recording URI")
    twilio_call_recording = fields.Binary(string="Twilio Call Recording")
    twilio_call_recording_filename = fields.Char(string="Twilio Call Recording Filename")
    record_model = fields.Char(string="Record Model", help="Name of the model this call was to e.g. res.partner / crm.lead")
    record_id = fields.Char(string="Record ID", help="ID of the record the call was to")

    @api.multi
    def add_twilio_call(self, call_sid):
        self.ensure_one()
        
        self.twilio_sid = call_sid

        #Fetch the recording for this call
        twilio_account = self.twilio_account_id
        response_string = requests.get("https://api.twilio.com/2010-04-01/Accounts/" + twilio_account.twilio_account_sid + "/Calls/" + call_sid + ".json", auth=(str(twilio_account.twilio_account_sid), str(twilio_account.twilio_auth_token)))

        call = json.loads(response_string.text)

        #Fetch the recording if it exists
        if 'subresource_uris' in call:
            if 'recordings' in call['subresource_uris']:
                if call['subresource_uris']['recordings'] != '':
                    recording_response = requests.get("https://api.twilio.com" + call['subresource_uris']['recordings'], auth=(str(twilio_account.twilio_account_sid), str(twilio_account.twilio_auth_token)))
                    recording_json = json.loads(recording_response.text)
                    for recording in recording_json['recordings']:
                        self.twilio_call_recording_uri = "https://api.twilio.com" + recording['uri'].replace(".json",".mp3")

        if 'price' in call:
            if call['price'] is not None:
                if float(call['price']) != 0.0:
                    self.currency_id = self.env['res.currency'].search([('name','=', call['price_unit'])])[0].id
                    self.price = -1.0 * float(call['price'])

        #Have to map the Twilio call status to the one in the core module
        twilio_status = call['status']
        if twilio_status == "queued":
            self.status = "pending"
        elif twilio_status == "ringing":
            self.status = "pending"
        elif twilio_status == "in-progress":
            self.status = "active"
        elif twilio_status == "canceled":
            self.status = "cancelled"
        elif twilio_status == "completed":
            self.status = "over"
        elif twilio_status == "failed":
            self.status = "failed"
        elif twilio_status == "busy":
            self.status = "busy"
        elif twilio_status == "no-answer":
            self.status = "failed"

        self.start_time = datetime.datetime.strptime(call['start_time'], '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')
        self.end_time = datetime.datetime.strptime(call['end_time'], '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')

        #Duration includes the ring time
        self.duration = call['duration']

        #Post to the chatter about the call
        #callee = self.env[voip_call.record_model].browse( int(voip_call.record_id) )
        #message_body = "A call was made using " + voip_call.twilio_number_id.name + " it lasted " + str(voip_call.duration) + " seconds"
        #my_message = callee.message_post(body=message_body, subject="Twilio Outbound Call")
        
        
class VoipCallComment(models.TransientModel):

    _name = "voip.call.comment"

    call_id = fields.Many2one('voip.call', string="Voip Call")
    note = fields.Html(string="Note")

    def post_feedback(self):
        message = self.env['mail.message']
        
        if self.call_id.record_model and self.call_id.record_id:
            record = self.env[self.call_id.record_model].browse(self.call_id.record_id)
        
            call_activity = self.env['ir.model.data'].get_object('mail','mail_activity_data_call')
            record_model = self.env['ir.model'].search([('model','=', self.call_id.record_model)])
            #Create an activity then mark it as done
            note = self.note + "<hr/>From Number: " + self.call_id.twilio_number_id.name

            #Chatter will sanitise html5 audo so instead place a url
            setting_record_calls = self.env['ir.default'].get('voip.settings','record_calls')
            if setting_record_calls:
                note += "<br/>Recording: " + '<a target="_blank" href="' +  self.call_id.twilio_call_recording_uri + '">Play Online</a>'

            mail_activity = self.env['mail.activity'].create({'res_model_id': record_model.id, 'res_id': self.call_id.record_id, 'activity_type_id': call_activity.id, 'note': note})
            mail_activity.action_feedback()