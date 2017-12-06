# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipSettingsTranscription(models.TransientModel):

    _inherit = 'voip.settings'
            
    transcriber_id = fields.Many2one('voip.transcriber', string="Transcriber")
    google_speech_recognition_api_key = fields.Char(string="Google Speech Recognition API Key")

    #-----Transcriber-----

    @api.multi
    def get_default_transcriber_id(self, fields):
        return {'transcriber_id': self.env['ir.values'].get_default('voip.settings', 'transcriber_id')}

    @api.multi
    def set_default_transcriber_id(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'transcriber_id', record.transcriber_id.id)
            
    #-----Google Speech Recognition API Key-----

    @api.multi
    def get_default_google_speech_recognition_api_key(self, fields):
        return {'google_speech_recognition_api_key': self.env['ir.values'].get_default('voip.settings', 'google_speech_recognition_api_key')}

    @api.multi
    def set_default_google_speech_recognition_api_key(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'google_speech_recognition_api_key', record.google_speech_recognition_api_key)