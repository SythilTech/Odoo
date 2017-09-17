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
from OpenSSL import crypto, SSL
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join
import os
from hashlib import sha256

from openerp import api, fields, models

class SIPSettings(models.Model):

    _name = "sip.settings"
    _inherit = 'res.config.settings'
            
    port = fields.Integer(string="Port")

    #-----Port-----

    @api.multi
    def get_default_port(self, fields):
        return {'port': self.env['ir.values'].get_default('sip.settings', 'port')}

    @api.multi
    def set_default_port(self):
        for record in self:
            self.env['ir.values'].set_default('sip.settings', 'port', record.port)
                        
    def start_sip_server(self):        
        voip_server = request.env['ir.model.data'].xmlid_to_object('voip_sip_webrtc_server.main_sip')
        voip_server.start_sip_server()
        
    def stop_sip_server(self):
        voip_server = request.env['ir.model.data'].xmlid_to_object('voip_sip_webrtc_server.main_sip')
        voip_server.stop_sip_server()