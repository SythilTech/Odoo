# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)
import werkzeug.utils
import werkzeug.wrappers
import werkzeug
import base64
import socket
from ast import literal_eval
import struct

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class VoipController(http.Controller):

    @http.route('/voip/window', type="http", auth="user")
    def voip_window(self):
        """ Returns a small popup window """

        return request.render("voip_sip_webrtc.voip_window")
        
    @http.route('/voip/ringtone/<voip_call_id>.mp3', type="http", auth="user")
    def voip_ringtone(self, voip_call_id):
        """Return the ringtone file to be used by javascript"""

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        to_user = request.env['res.users'].search([('partner_id','=',voip_call.partner_id.id)])

        #Check if the callee has a person ringtone set
        if to_user.voip_ringtone:
            ringtone_media = to_user.voip_ringtone
        else:
            voip_ringtone_id = request.env['ir.default'].get('voip.settings', 'ringtone_id')
            voip_ringtone = request.env['voip.ringtone'].browse( voip_ringtone_id )
            ringtone_media = voip_ringtone.media

        headers = []
        ringtone_base64 = base64.b64decode(ringtone_media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response

    @http.route('/voip/messagebank/<voip_call_id>', type="http", auth="user")
    def voip_messagebank(self, voip_call_id):
        """ Allow listen to call in browser """

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )

        html = ""

        if voip_call.server_stream_data:
            html += "<b>Server Stream: </b><br/>"
            html += "<audio controls=\"controls\" autoplay=\"autoplay\" controlsList=\"nodownload\">\n"
            html += "  <source src=\"/voip/messagebank/server/" + str(voip_call.id) + ".wav\" type=\"audio/wav\">\n"
            html += "</audio><br/>\n"

        for voip_client in voip_call.client_ids:
            html += "<b>Client " + voip_client.name + " Stream</b><br/>"
            html += "<audio controls=\"controls\" autoplay=\"autoplay\" controlsList=\"nodownload\">\n"
            html += "  <source src=\"/voip/messagebank/client/" + str(voip_client.id) + ".wav\" type=\"audio/wav\">\n"
            html += "</audio><br/>\n"

        return html

    @http.route('/voip/messagebank/client/<voip_call_client_id>.wav', type="http", auth="user")
    def voip_messagebank_client(self, voip_call_client_id):
        """ Allow listen to call in browser """

        voip_call_client = request.env['voip.call.client'].browse( int(voip_call_client_id) )
        voip_call = voip_call_client.vc_id

        headers = []
        audio_stream = base64.b64decode(voip_call_client.audio_stream)

        #Add a RIFF wrapper to the raw file so we can play the audio in the browser, this is just a crude solution for those that don't have transcoding installed
        if voip_call_client.vc_id.media_filename == "call.raw":
            #"RIFF"
            riff_wrapper = "52 49 46 46"
            #File Size
            riff_wrapper += " " + struct.pack('<I', len(audio_stream) - 8 ).encode('hex')
            #"WAVE"
            riff_wrapper += " 57 41 56 45"
            #"fmt "
            riff_wrapper += " 66 6D 74 20"
            #Subchunk1Size(18)
            riff_wrapper += " 12 00 00 00"
            #AudioFormat (7) ulaw
            #riff_wrapper += " 07 00"
            riff_wrapper += struct.pack('<H', voip_call.codec_id.riff_audio_encoding_value ).encode('hex')
            #NumChannels(1)
            riff_wrapper += " 01 00"
            #Sample rate (8000)
            riff_wrapper += " 40 1F 00 00"
            #ByteRate (SampleRate[8000] * NumChannels[1] * BitsPerSample[8]/8 = 16000)
            riff_wrapper += " 40 1F 00 00"
            #BlockAlign (NumChannels[1] * BitsPerSample[8]/8)
            riff_wrapper += " 01 00"
            #BitsPerSample(8)
            riff_wrapper += " 08 00"
            #No idea
            riff_wrapper += " 00 00"
            #Subchunk2ID "data"
            riff_wrapper += "64 61 74 61"
            #Subchunk2Size (NumSamples * NumChannels[1] * BitsPerSample[8])
            riff_wrapper += " " + struct.pack('<I', len(audio_stream) - 46 ).encode('hex')
            media = riff_wrapper.replace(" ","").decode('hex') + audio_stream

        headers.append(('Content-Length', len(media)))
        headers.append(('Content-Type', 'audio/x-wav'))
        response = request.make_response(media, headers)

        return response

    @http.route('/voip/messagebank/server/<voip_call_id>.wav', type="http", auth="user")
    def voip_messagebank_server(self, voip_call_id):
        """ Audio generated by the server """

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )

        headers = []
        audio_stream = base64.b64decode(voip_call.server_stream_data)

        #Add a RIFF wrapper to the raw file so we can play the audio in the browser, this is just a crude solution for those that don't have transcoding installed
        if voip_call.media_filename == "call.raw":
            #"RIFF"
            riff_wrapper = "52 49 46 46"
            #File Size
            riff_wrapper += " " + struct.pack('<I', len(audio_stream) - 8 ).encode('hex')
            #"WAVE"
            riff_wrapper += " 57 41 56 45"
            #"fmt "
            riff_wrapper += " 66 6D 74 20"
            #Subchunk1Size(18)
            riff_wrapper += " 12 00 00 00"
            #AudioFormat (7) ulaw
            #riff_wrapper += " 07 00"
            riff_wrapper += struct.pack('<H', voip_call.codec_id.riff_audio_encoding_value ).encode('hex')
            #NumChannels(1)
            riff_wrapper += " 01 00"
            #Sample rate (8000)
            riff_wrapper += " 40 1F 00 00"
            #ByteRate (SampleRate[8000] * NumChannels[1] * BitsPerSample[8]/8 = 16000)
            riff_wrapper += " 40 1F 00 00"
            #BlockAlign (NumChannels[1] * BitsPerSample[8]/8)
            riff_wrapper += " 01 00"
            #BitsPerSample(8)
            riff_wrapper += " 08 00"
            #No idea
            riff_wrapper += " 00 00"
            #Subchunk2ID "data"
            riff_wrapper += "64 61 74 61"
            #Subchunk2Size (NumSamples * NumChannels[1] * BitsPerSample[8])
            riff_wrapper += " " + struct.pack('<I', len(audio_stream) - 46 ).encode('hex')
            media = riff_wrapper.replace(" ","").decode('hex') + audio_stream

        headers.append(('Content-Length', len(media)))
        headers.append(('Content-Type', 'audio/x-wav'))
        response = request.make_response(media, headers)

        return response

    @http.route('/voip/miss/<voip_call_id>.mp3', type="http", auth="user")
    def voip_miss_message(self, voip_call_id):
        """ Play the missed call mp3 of the callee """

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        to_user = request.env['res.users'].search([('partner_id','=',voip_call.partner_id.id)])

        if to_user.voip_missed_call:
            missed_call_media = to_user.voip_missed_call

            headers = []
            missed_call_media_base64 = base64.b64decode(missed_call_media)
            headers.append(('Content-Length', len(missed_call_media_base64)))
            response = request.make_response(missed_call_media_base64, headers)

            return response
        else:
            #TODO read blank.mp3 and return it
            return ""