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