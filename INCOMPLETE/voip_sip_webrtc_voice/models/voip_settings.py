# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipSettingsVoice(models.TransientModel):

    _inherit = 'voip.settings'

    bing_tts_api_key = fields.Char(string="Bing TTS API Key")

    @api.multi
    def set_values(self):
        super(VoipSettingsVoice, self).set_values()
        self.env['ir.default'].set('voip.settings', 'bing_tts_api_key', self.bing_tts_api_key)

    @api.model
    def get_values(self):
        res = super(VoipSettingsVoice, self).get_values()
        res.update(
            bing_tts_api_key=self.env['ir.default'].get('voip.settings', 'bing_tts_api_key'),
        )
        return res