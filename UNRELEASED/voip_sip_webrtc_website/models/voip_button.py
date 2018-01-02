# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class VoipButton(models.Model):

    _name = 'voip.button'

    name = fields.Char(string="Name")
    url = fields.Char(string="URL", help="The URL the button was placed on, has not functional purpose")
    user_id = fields.Many2one('res.users', string="Call User")