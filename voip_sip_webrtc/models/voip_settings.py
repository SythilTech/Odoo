# -*- coding: utf-8 -*-
import socket
import threading
import random
import string
import logging
import requests
_logger = logging.getLogger(__name__)
from openerp.http import request
import odoo
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join
import os
import struct
from hashlib import sha256

from openerp import api, fields, models

class VoipSettings(models.Model):

    _name = "voip.settings"
    _inherit = 'res.config.settings'
            
    ringtone_id = fields.Many2one('voip.ringtone', string="Ringtone", required=True)
    ring_duration = fields.Integer(string="Ring Duration (Seconds)", required=True)
    server_ip = fields.Char(string="IP Address")
    inactivity_time = fields.Integer(string="Inactivity Time (Minutes)", help="The amount of minutes before the user is considered offline", required=True)
    record_calls = fields.Boolean(string="Record SIP Calls")
    codec_id = fields.Many2one('voip.codec', string="Default Codec", help="When a call is accepted it specifies to use this codec, all media should be pre-transcoded in this codec ready to be streamed", required=True)

    def find_outgoing_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.server_ip = s.getsockname()[0]
        s.close()

    @api.multi
    def set_values(self):
        super(VoipSettings, self).set_values()
        self.env['ir.default'].set('voip.settings', 'ringtone_id', self.ringtone_id.id)
        self.env['ir.default'].set('voip.settings', 'ring_duration', self.ring_duration)
        self.env['ir.default'].set('voip.settings', 'server_ip', self.server_ip)
        self.env['ir.default'].set('voip.settings', 'inactivity_time', self.inactivity_time)
        self.env['ir.default'].set('voip.settings', 'record_calls', self.record_calls)
        self.env['ir.default'].set('voip.settings', 'codec_id', self.codec_id.id)
        
    @api.model
    def get_values(self):
        res = super(VoipSettings, self).get_values()
        res.update(
            ringtone_id=self.env['ir.default'].get('voip.settings', 'ringtone_id'),
            ring_duration=self.env['ir.default'].get('voip.settings', 'ring_duration'),
            server_ip=self.env['ir.default'].get('voip.settings', 'server_ip'),
            inactivity_time=self.env['ir.default'].get('voip.settings', 'inactivity_time'),
            record_calls=self.env['ir.default'].get('voip.settings', 'record_calls'),
            codec_id=self.env['ir.default'].get('voip.settings', 'codec_id')
        )
        return res



