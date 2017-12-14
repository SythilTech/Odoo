# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipMedia(models.Model):

    _name = "voip.media"

    name = fields.Char(string="Name")
    media = fields.Binary(string="Media File")
    media_filename = fields.Char(string="Media Filename")
    codec_id = fields.Many2one('voip.codec', string="Codec")