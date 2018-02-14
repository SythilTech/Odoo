# -*- coding: utf-8 -*-
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
from lxml import etree
import re
from odoo.exceptions import UserError

from openerp import api, fields, models

class VoipMessageCompose(models.TransientModel):

    _name = "voip.message.compose"

    type = fields.Char(string="Message Type")
    sip_account_id = fields.Many2one('voip.account', string="SIP Account")
    message_template_id = fields.Many2one('voip.message.template', string="Message Template")
    partner_id = fields.Many2one('res.partner', string="Partner (OBSOLETE)")
    model = fields.Char(string="Model")
    record_id = fields.Integer(string="Record ID")
    to_address = fields.Char(string="To Address")
    message = fields.Text(string="Message")
    
    @api.onchange('message_template_id')
    def _onchange_message_template_id(self):
        self.message = self.message_template_id.message
    
    def send_message(self):

        method = '_send_%s_message' % (self.type,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        action()
        
    def _send_sip_message(self):

        message_response = self.sip_account_id.send_message(self.to_address, self.message, model=self.model, record_id=self.record_id)
        
        if message_response != "OK":
            _logger.error("SIP Message Failure")
            raise UserError("Failed to send SIP message: " + message_response)