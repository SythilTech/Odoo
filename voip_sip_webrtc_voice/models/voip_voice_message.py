# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models, tools

class VoipVoiceMessage(models.Model):

    _name = "voip.voice.message"

    name = fields.Char(string="Name")
    voice_synth_id = fields.Many2one('voip.voice', string="Voice Synthesizer")
    synth_text = fields.Text(string="Synth Text")
    
    def synth_message(self, codec_id):
        return self.voice_synth_id.voice_synth(self.synth_text, codec_id)