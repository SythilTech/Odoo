# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import subprocess
import tempfile
from openerp import api, fields, models, tools

class VoipCallTemplateInheritVoice(models.Model):

    _inherit = "voip.call.template"

    type = fields.Selection(selection_add=[('synth','Voice Synthesis')])
    voice_synth_id = fields.Many2one('voip.voice', string="Voice Synthesizer")
    synth_text = fields.Text(string="Synth Text")

    def voice_synth(self, rendered_text, to_address, record_id):
        
        #each field type has it's own function that way we can make plugin modules with new field types
        method = '_synth_%s' % (self.voice_synth_id.internal_code,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        action(rendered_text, to_address, record_id,)
        
    def _synth_espeak(self, rendered_text, to_address, record_id):

        voice_synth_file_path = "/odoo/voice.wav"
        subprocess.call(["espeak", "-w" + voice_synth_file_path, rendered_text])
            
        #Transcode the file
        output_filepath = tempfile.gettempdir() + "/output.raw"
        subprocess.call(['sox', voice_synth_file_path, "--rate", str(self.codec_id.sample_rate), "--channels", "1", "--encoding", self.codec_id.encoding, "--type","raw", output_filepath])  
            
        #Read the transcoded file
        file_content = open(output_filepath, 'rb').read()

        self.voip_account_id.make_call(to_address, file_content, self.codec_id, self.model_id.model, record_id)       
