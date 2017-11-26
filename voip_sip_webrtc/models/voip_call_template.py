# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class VoipCallTemplate(models.Model):

    _name = "voip.call.template"

    name = fields.Char(string="Name")
    voip_account_id = fields.Many2one('voip.account', string="VOIP Account")
    to_address = fields.Char(string="To Address", help="Use placeholders")
    