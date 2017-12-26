# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
import subprocess
import shutil
import tempfile

from openerp import api, fields, models, tools

class VoipVoice(models.Model):

    _name = "voip.voice"

    name = fields.Char(string="Name")
    internal_code = fields.Char(string="Internal Code")
    
    def voice_synth(self, rendered_text, codec_id):

        #each field type has it's own function that way we can make plugin modules with voice synth types
        method = '_synth_%s' % (self.internal_code,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        return action(rendered_text, codec_id,)

    def _synth_espeak(self, rendered_text, codec_id):

        voice_synth_file_path = "/odoo/voice.wav"
        subprocess.call(["espeak", "-w" + voice_synth_file_path, rendered_text])

        #Transcode the file
        output_filepath = tempfile.gettempdir() + "/output.raw"
        subprocess.call(['sox', voice_synth_file_path, "--rate", str(codec_id.sample_rate), "--channels", "1", "--encoding", codec_id.encoding, "--type","raw", output_filepath])

        #Read the transcoded file
        return open(output_filepath, 'rb').read()

    def _synth_bing(self, rendered_text, codec_id):

        api_key = self.env['ir.values'].get_default('voip.settings', 'bing_tts_api_key')
        
        #Get access token
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        auth_response = requests.post("https://api.cognitive.microsoft.com/sts/v1.0/issueToken", headers=headers)
        access_token = auth_response.text

        headers = {}
        headers['Content-type'] = "application/ssml+xml"
        headers['X-Microsoft-OutputFormat'] = "riff-16khz-16bit-mono-pcm"
        headers['Authorization'] = "Bearer " + access_token
        headers['X-Search-AppId'] = "07D3234E49CE426DAA29772419F436CA"
        headers['X-Search-ClientID'] = "1ECFAE91408841A480F00935DC390960"
        headers['User-Agent'] = "TTSForPython"

        synth_string = "<speak version='1.0' xml:lang='en-US'><voice xml:lang='en-US' xml:gender='Female' name='Microsoft Server Speech Text to Speech Voice (en-AU, HayleyRUS)'>" + rendered_text + "</voice></speak>"
        synth_response = requests.post("https://speech.platform.bing.com/synthesize", data=synth_string, headers=headers, stream=True)
        
        with open("/odoo/ms.wav", "wb") as out_file:
            shutil.copyfileobj(synth_response.raw, out_file)
        
            output_filepath = tempfile.gettempdir() + "/output.raw"
            subprocess.call(['sox', "/odoo/ms.wav", "--rate", str(codec_id.sample_rate), "--channels", "1", "--encoding", codec_id.encoding, "--type","raw", output_filepath])

            #Read the transcoded file
            return open(output_filepath, 'rb').read()
            