# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class VoipMessageCompose(models.TransientModel):

    _name = "voip.message.compose"

    type = fields.Char(string="Message Type")
    partner_id = fields.Many2one('res.partner', string="Partner")
    message = fields.Text(string="Message")
    
    def send_message(self):
        _logger.error("Send Message")