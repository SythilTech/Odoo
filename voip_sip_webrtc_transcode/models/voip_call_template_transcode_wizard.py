# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import base64
import subprocess
import tempfile

from openerp import api, fields, models

class VoipCallTemplateTranscodeWizard(models.TransientModel):

    _name = 'voip.call.template.transcode.wizard'
    _description = "OBSOLETE"
    
    call_template_id = fields.Many2one('voip.call.template', string="Call Template")
    media = fields.Binary(string="Audio File", required="True")
    media_filename = fields.Char(string="Audio File Filename")
    codec_id = fields.Many2one('voip.codec', string="Codec", required="True")
    
    def transcode(self):
        _logger.error("Transcode")
        
        with tempfile.NamedTemporaryFile(suffix='.' + self.media_filename.split(".")[-1]) as tmp:
            #Write the media to a temp file
            tmp.write( base64.decodestring(self.media) )
            
            #Transcode the file
            output_filepath = tempfile.gettempdir() + "/output.raw"
            subprocess.call(['sox', tmp.name, "--rate", str(self.codec_id.sample_rate), "--channels", "1", "--encoding", self.codec_id.encoding, "--type","raw", output_filepath])  
            
            #Read the transcoded file
            file_content = open(output_filepath, 'rb').read()
            
            #Save the transcoded file to the call template
            self.call_template_id.media = base64.encodestring(file_content)
            self.call_template_id.codec_id = self.codec_id.id
            
            #Clean up temp file
            tmp.close()
            
            #TODO cleanup output.raw
            
        