# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipCodec(models.Model):

    _name = "voip.codec"

    name = fields.Char(string="Name")
    payload_type = fields.Integer(string="Payload Type")
    encoding = fields.Char(string="Encoding")
    sample_rate = fields.Integer(string="Sample Rate")
    supported = fields.Boolean(string="Supported")    