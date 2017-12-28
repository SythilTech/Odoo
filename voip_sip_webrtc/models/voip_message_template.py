# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class VoipMessageTemplate(models.Model):

    _name = "voip.message.template"

    name = fields.Char(string="Name")
    template_body = fields.Text(string="Body")