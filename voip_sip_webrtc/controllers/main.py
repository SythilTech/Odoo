# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)
import werkzeug.utils
import werkzeug.wrappers
import urllib2
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
        
    @http.route('/voip/ringtone/<voip_call_id>.mp3', type="http", auth="user")
    def voip_ringtone(self, voip_call_id):
        """Return the ringtone file to be used by javascript"""

        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        to_user = request.env['res.users'].search([('partner_id','=',voip_call.partner_id.id)])
        
        #Check if the callee has a person ringtone set
        if to_user.voip_ringtone:
            ringtone_media = to_user.voip_ringtone
        else:
            voip_ringtone_id = request.env['ir.values'].get_default('voip.settings', 'ringtone_id')
            voip_ringtone = request.env['voip.ringtone'].browse( voip_ringtone_id )
            ringtone_media = voip_ringtone.media

        headers = []
        ringtone_base64 = base64.b64decode(ringtone_media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response

    @http.route('/voip/messagebank/<voip_call_id>.wav', type="http", auth="user")
    def voip_messagebank(self, voip_call_id):
        """ Allow listen to call in browser """
        
        voip_call = request.env['voip.call'].browse( int(voip_call_id) )
        
        headers = []
        media_base64 = base64.b64decode(voip_call.media)

        #Add a RIFF wrapper to the raw file so we can play the audio in the browser, this is just a crude solution for those that don't have transcoding installed        
        if voip_call.media_filename == "call.raw":
            riff_wrapper = "52 49 46 46"
	    riff_wrapper += " " + struct.pack('<I', len(media_base64) - 8 ).encode('hex')
	    riff_wrapper += " 57 41 56 45 66 6D 74 20 12 00 00 00 06 00 01 00 40 1F 00 00 40 1F 00 00 01 00 08 00 00 00 66 61 63 74 04 00 00 00 00 48 18 00 4C 49 53 54 1A 00 00 00 49 4E 46 4F 49 53 46 54 0E 00 00 00 4C 61 76 66 35 35 2E 33 33 2E 31 30 30 00 64 61 74 61"
	    riff_wrapper += " " + struct.pack('<I', len(media_base64) - 44 ).encode('hex')
	    media_base64 = riff_wrapper.replace(" ","").decode('hex') + media_base64

        headers.append(('Content-Length', len(media_base64)))
        headers.append(('Content-Type', 'audio/x-wav'))
        response = request.make_response(media_base64, headers)

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