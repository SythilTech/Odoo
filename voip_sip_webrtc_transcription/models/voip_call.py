# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import tempfile
import base64
import speech_recognition as sr
    
from openerp import api, fields, models
from odoo.exceptions import UserError
import subprocess

class VoipCallTranscription(models.Model):

    _inherit = 'voip.call'

    def transcribe(self, transcriber):


        r = sr.Recognizer()

        tmp = tempfile.NamedTemporaryFile()
        tmp.write(base64.decodestring(self.media))        

        #subprocess.call(['sox', tmp.name, "--rate", str(self.codec_id.sample_rate), "--channels", "1", "--encoding", self.codec_id.encoding, "--type","raw", output_filepath])  

        output_filepath = tempfile.gettempdir() + "/output.flac"        
        subprocess.call(['sox', "--rate", str(self.codec_id.sample_rate), "--channels", "1", "--encoding", self.codec_id.encoding, "--type","raw", tmp.name, output_filepath])  

        #with sr.AudioFile(tmp.name) as source:
        with sr.AudioFile(output_filepath) as source:
            audio = r.record(source)  # read the entire audio file

        #each field type has it's own function that way we can make plugin modules with new field types
        method = '_recognize_%s' % (transcriber.internal_code,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        self.transcription = action(r, audio, )

        tmp.close()

    def _recognize_cmu_sphinx(self, audio):

        try:
            return r.recognize_sphinx(audio)
        except sr.UnknownValueError:
            raise UserError("Sphinx could not understand audio")
        except sr.RequestError as e:
            raise UserError("Sphinx error; {0}".format(e))
    
    def _recognize_google_speech_recognition(self, r, audio):
        setting_google_speech_recognition_api_key = self.env['ir.values'].get_default('voip.settings', 'google_speech_recognition_api_key')
            
        try:
            if setting_google_speech_recognition_api_key:
                return r.recognize_google(audio, key=setting_google_speech_recognition_api_key)
            else:
	        return r.recognize_google(audio)
	except sr.UnknownValueError:
	    raise UserError("Google Speech Recognition could not understand audio")
	except sr.RequestError as e:
            raise UserError("Could not request results from Google Speech Recognition service; {0}".format(e))
                
    def _recognize_google_cloud_speech_api(self, r, audio):
        #TODO actually code this
        GOOGLE_CLOUD_SPEECH_CREDENTIALS = "INSERT THE CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE"

        try:
            return r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS)
        except sr.UnknownValueError:
            raise UserError("Google Cloud Speech could not understand audio")
        except sr.RequestError as e:
            raise UserError("Could not request results from Google Cloud Speech service; {0}".format(e))

    def _recognize_wit_ai(self, r, audio):        
        #TODO actually code this
        #setting_transcriber_api_key = self.env['ir.values'].get_default('voip.settings', 'transcriber_api_key')
            
        try:
            return r.recognize_wit(audio, key=setting_transcriber_api_key)
        except sr.UnknownValueError:
            raise UserError("Wit.ai could not understand audio")
        except sr.RequestError as e:
            raise UserError("Could not request results from Wit.ai service; {0}".format(e))
                
    def _recognize_microsoft_bing_voice_recognition(self, r, audio):
        #TODO actually code this
        #setting_transcriber_api_key = self.env['ir.values'].get_default('voip.settings', 'transcriber_api_key')

        try:
            return r.recognize_bing(audio, key=setting_transcriber_api_key)
        except sr.UnknownValueError:
            raise UserError("Microsoft Bing Voice Recognition could not understand audio")
        except sr.RequestError as e:
            raise UserError("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))
                
    def _recognize_houndify_api(self, r, audio):
        #TODO actually code this
        HOUNDIFY_CLIENT_ID = "INSERT HOUNDIFY CLIENT ID HERE"
        HOUNDIFY_CLIENT_KEY = "INSERT HOUNDIFY CLIENT KEY HERE"

        try:
            return r.recognize_houndify(audio, client_id=HOUNDIFY_CLIENT_ID, client_key=HOUNDIFY_CLIENT_KEY)
        except sr.UnknownValueError:
            raise UserError("Houndify could not understand audio")
        except sr.RequestError as e:
            raise UserError("Could not request results from Houndify service; {0}".format(e))        

    def _recognize_ibm_speech_to_text(self, r, audio):
        #TODO actually code
        IBM_USERNAME = "INSERT IBM SPEECH TO TEXT USERNAME HERE"
        IBM_PASSWORD = "INSERT IBM SPEECH TO TEXT PASSWORD HERE"

        try:
	    return r.recognize_ibm(audio, username=IBM_USERNAME, password=IBM_PASSWORD)
	except sr.UnknownValueError:
	    raise UserError("IBM Speech to Text could not understand audio")
	except sr.RequestError as e:
            raise UserError("Could not request results from IBM Speech to Text service; {0}".format(e))