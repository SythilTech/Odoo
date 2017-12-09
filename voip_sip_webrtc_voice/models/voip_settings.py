# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipSettingsVoice(models.TransientModel):

    _inherit = 'voip.settings'
            
    voice_synth_id = fields.Many2one('voip.voice', string="Voice Synthesizer")

    #-----Voice Synthesizer-----

    @api.multi
    def get_default_voice_synth_id(self, fields):
        return {'voice_synth_id': self.env['ir.values'].get_default('voip.settings', 'voice_synth_id')}

    @api.multi
    def set_default_voice_synth_id(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'voice_synth_id', record.voice_synth_id.id)
            