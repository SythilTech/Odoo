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
            
    missed_call_action = fields.Selection([('nothing', 'Nothing')], string="Missed Call Action", help="What action is taken when the call is missed")
    ringtone_id = fields.Many2one('voip.ringtone', string="Ringtone")
    ringtone = fields.Binary(string="Default Ringtone")
    ringtone_filename = fields.Char("Ringtone Filename")
    ring_duration = fields.Integer(string="Ring Duration (Seconds)")
    server_ip = fields.Char(string="IP Address")

    @api.multi
    def set_values(self):
        super(VoipSettings, self).set_values()
        self.env['ir.default'].set('voip.settings', 'ringtone_id', self.ringtone_id.id)
        self.env['ir.default'].set('voip.settings', 'ring_duration', self.ring_duration)
        self.env['ir.default'].set('voip.settings', 'server_ip', self.server_ip)

    @api.model
    def get_values(self):
        res = super(VoipSettings, self).get_values()
        res.update(
            ringtone_id=self.env['ir.default'].get('voip.settings', 'ringtone_id'),
            ring_duration=self.env['ir.default'].get('voip.settings', 'ring_duration'),
            server_ip=self.env['ir.default'].get('voip.settings', 'server_ip')
        )
        return res



