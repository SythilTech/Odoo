# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

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
        #Send notification to self to start the Twilio javascript client
        notification = {'from_number': self.from_number.number, 'to_number': self.to_number, 'capability_token_url': self.from_number.capability_token_url}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.twilio.start', self.env.user.partner_id.id), notification)
        _logger.error(self.env.user.name)