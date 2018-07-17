# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import datetime

from odoo import api, fields, models

class VoipCallWizard(models.Model):

    _name = "voip.call.wizard"
    _description = "Twilio Call Wizard"

    record_model = fields.Char(string="Record Model")
    record_id = fields.Integer(string="Record ID")
    partner_id = fields.Many2one('res.partner')
    from_number = fields.Many2one('voip.number', string="From Number")
    to_number = fields.Char(string="To Number", readonly="True")
    
    def start_call(self):
    
        #Create the call record now
        voip_call = self.env['voip.call'].create({'status': 'pending', 'twilio_number_id': self.from_number.id, 'twilio_account_id': self.from_number.account_id.id, 'from_address': self.from_number.number, 'from_partner_id': self.env.user.partner_id.id, 'to_address': self.to_number, 'to_partner_id': self.partner_id.id, 'ring_time': datetime.datetime.now(), 'record_model': self.record_model, 'record_id': self.record_id})
        
        #Send notification to self to start the Twilio javascript client
        notification = {'from_number': self.from_number.number, 'to_number': self.to_number, 'capability_token_url': self.from_number.capability_token_url, 'call_id': voip_call.id}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.twilio.start', self.env.user.partner_id.id), notification)