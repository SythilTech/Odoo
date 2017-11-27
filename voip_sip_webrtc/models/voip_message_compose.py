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
    partner_id = fields.Many2one('res.partner', string="Partner (Old)")
    model = fields.Char(string="Model")
    record_id = fields.Integer(string="Record ID")
    to_address = fields.Char(string="To Address")
    message = fields.Text(string="Message")
        
    def send_message(self):

        method = '_send_%s_message' % (self.type,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        action()
        
    def _send_sip_message(self):

        if self.sip_account_id.send_message(self.to_address, self.message, model=self.model, record_id=self.record_id):
            _logger.error("SIP Message Sent")
        else:
            _logger.error("SIP Message Failure")
            raise UserError("Failed to send SIP message")