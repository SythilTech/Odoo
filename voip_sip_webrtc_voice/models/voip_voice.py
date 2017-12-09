# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models, tools

class VoipVoice(models.Model):

    _name = "voip.voice"

    name = fields.Char(string="Name")
    internal_code = fields.Char(string="Internal Code")