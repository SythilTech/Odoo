# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models
import json

import requests
from openerp.http import request

class VoipNumber(models.Model):

    _name = "voip.number"

    name = fields.Char(string="Name")
    number = fields.Char(string="Number")
    account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    capability_token_url = fields.Char(string="Capability Token URL")
    twilio_app_id = fields.Char(string="Twilio App ID")
    call_routing_ids = fields.Many2many('res.users', string="Call Routing")
    
    @api.model
    def get_numbers(self, **kw):
        """ Get the numbers that the user can receive calls from """

        call_routes = []
        for call_route in self.env.user.call_routing_ids:
            call_routes.append({'capability_token_url': call_route.capability_token_url})
        
        return call_routes
        
    def create_twilio_app(self):
        
        #Create the application for the number and point it back to the server
        data = {'FriendlyName': 'Auto Setup Application for ' + str(self.name), 'VoiceUrl': request.httprequest.host_url + 'twilio/voice/route'}
        response_string = requests.post("https://api.twilio.com/2010-04-01/Accounts/" + self.account_id.twilio_account_sid + "/Applications.json", data=data, auth=(str(self.account_id.twilio_account_sid), str(self.account_id.twilio_auth_token)))
        response_string_json = json.loads(response_string.content.decode('utf-8'))

        self.twilio_app_id = response_string_json['sid']

        self.capability_token_url = request.httprequest.host_url + 'twilio/capability-token/' + str(self.id)