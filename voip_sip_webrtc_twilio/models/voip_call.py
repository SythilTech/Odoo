# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models

class VoipCallInheritTWilio(models.Model):

    _inherit = "voip.call"

    twilio_sid = fields.Char(string="Twilio SID")