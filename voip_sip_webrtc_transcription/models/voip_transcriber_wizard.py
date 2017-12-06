# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipTranscriberWizard(models.TransientModel):

    _name = 'voip.transcriber.wizard'
            
    call_id = fields.Many2one('voip.call', string="VOIP Call")
    transcriber_id = fields.Many2one('voip.transcriber', string="Transcriber")
    
    def wizard_transcribe(self):
        self.call_id.transcribe(self.transcriber_id)