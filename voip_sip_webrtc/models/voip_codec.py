# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipCodec(models.Model):

    _name = "voip.codec"

    name = fields.Char(string="Name")
    payload_type = fields.Integer(string="Payload Type")
    encoding = fields.Char(string="Encoding")
    sample_rate = fields.Integer(string="Sample Rate")
    payload_size = fields.Integer(string="Payload Size")
    sample_interval = fields.Integer(string="Sample Interval")
    supported = fields.Boolean(string="Supported")
    sdp_data = fields.Char(string="SDP Data")
    riff_audio_encoding_value = fields.Integer("RIFF Audio Encoding Value")