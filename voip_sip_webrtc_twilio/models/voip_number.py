# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models

class VoipNumber(models.Model):

    _name = "voip.number"

    name = fields.Char(string="Name")
    number = fields.Char(string="Number")
    account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    capability_token_url = fields.Char(string="Capability Token URL")
    call_routing_ids = fields.Many2many('res.users', string="Call Routing")
    
    @api.model
    def get_numbers(self, **kw):
        """ Get the numbers that the user can receive calls from """

        call_routes = []
        for call_route in self.env.user.call_routing_ids:
            call_routes.append({'capability_token_url': call_route.capability_token_url})
        
        return call_routes