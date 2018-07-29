# -*- coding: utf-8 -*-
import socket
import logging
from openerp.exceptions import UserError
_logger = logging.getLogger(__name__)
from openerp.http import request
import re
import hashlib
import random
from openerp import api, fields, models
import threading
import time
import datetime
import struct
import base64
from random import randint
            
class VoipAccountActionInheritVoice(models.Model):

    _inherit = "voip.account.action"

    voip_voice_message_id = fields.Many2one('voip.voice.message', string="Voice Message")

    def _voip_action_initialize_voice_message(self, voip_call_client):
        _logger.error("Change Action Voice Synth")
        codec_id = self.env['ir.model.data'].sudo().get_object('voip_sip_webrtc', 'pcmu')
        audio_stream = self.voip_voice_message_id.synth_message(codec_id, voip_call_client.id)
        return audio_stream

    def _voip_action_sender_voice_message(self, media_data, media_index, payload_size):
        rtp_payload_data = media_data[media_index * payload_size : media_index * payload_size + payload_size]
        new_media_index = media_index + 1
        return rtp_payload_data, media_data, new_media_index