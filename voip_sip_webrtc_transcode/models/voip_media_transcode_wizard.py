# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import base64
import subprocess
import tempfile

from openerp import api, fields, models

class VoipMediaTranscodeWizard(models.TransientModel):

    _name = 'voip.media.transcode.wizard'

    media_id = fields.Many2one('voip.media', string="Media")
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
            
            #Save the transcoded file to the media template
            self.media_id.media = base64.encodestring(file_content)
            self.media_id.media_filename = self.media_filename
            self.media_id.codec_id = self.codec_id.id
            
            #Clean up temp file
            tmp.close()
            
            #TODO cleanup output.raw
            
        