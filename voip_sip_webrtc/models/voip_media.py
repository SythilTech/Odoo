# -*- coding: utf-8 -*-
from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class VoipMedia(models.Model):

    _name = "voip.media"

    @api.model
    def _get_default_codec_id(self):
        return self.env['ir.default'].get('voip.settings','codec_id')

    name = fields.Char(string="Name")
    media = fields.Binary(string="Media File")
    media_filename = fields.Char(string="Media Filename")
    codec_id = fields.Many2one('voip.codec', default=_get_default_codec_id, string="Codec")