# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models

class VoipCallInheritTWilio(models.Model):

    _inherit = "voip.call"

    twilio_sid = fields.Char(string="Twilio SID")
    twilio_account_id = fields.Many2one('voip.twilio', string="Twilio Account")
    currency_id = fields.Many2one('res.currency', string="Currency")
    price = fields.Float(string="Price")
    margin = fields.Float(string="Margin")