# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class VoipRingtone(models.Model):

    _name = "voip.ringtone"

    media = fields.Binary(string="Media File")