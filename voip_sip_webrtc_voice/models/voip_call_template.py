# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models, tools

class VoipCallTemplateInheritVoice(models.Model):

    _inherit = "voip.call.template"

    type = fields.Selection(selection_add=[('synth','Voice Synthesis')])
    voice_synth_id = fields.Many2one('voip.voice', string="Voice Synthesizer")
    synth_text = fields.Text(string="Synth Text")