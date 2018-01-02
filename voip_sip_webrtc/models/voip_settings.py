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
    message_bank_duration = fields.Integer(string="Message Bank Duration (Seconds)", help="The time before message bank automatically hangs up")
    server_ip = fields.Char(string="IP Address")
    cert_path = fields.Char(string="Cert Path", help="Used by message bank")
    key_path = fields.Char(string="Key Path", help="Used by message bank")
    fingerprint = fields.Char(string="Fingerprint", help="Used by message bank")

    #-----Ringtone ID-----

    @api.multi
    def get_default_ringtone_id(self, fields):
        return {'ringtone_id': self.env['ir.values'].get_default('voip.settings', 'ringtone_id')}

    @api.multi
    def set_default_ringtone_id(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'ringtone_id', record.ringtone_id.id)

    #-----Ring Duration-----

    @api.multi
    def get_default_ring_duration(self, fields):
        return {'ring_duration': self.env['ir.values'].get_default('voip.settings', 'ring_duration')}

    @api.multi
    def set_default_ring_duration(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'ring_duration', record.ring_duration)


    #-----Message Bank Duration-----

    @api.multi
    def get_default_message_bank_duration(self, fields):
        return {'message_bank_duration': self.env['ir.values'].get_default('voip.settings', 'message_bank_duration')}

    @api.multi
    def set_default_message_bank_duration(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'message_bank_duration', record.message_bank_duration)

    #-----Server IP-----

    @api.multi
    def get_default_server_ip(self, fields):
        return {'server_ip': self.env['ir.values'].get_default('voip.settings', 'server_ip')}

    @api.multi
    def set_default_server_ip(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'server_ip', record.server_ip)

    #-----Cert Path-----

    @api.multi
    def get_default_cert_path(self, fields):
        return {'cert_path': self.env['ir.values'].get_default('voip.settings', 'cert_path')}

    @api.multi
    def set_default_cert_path(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'cert_path', record.cert_path)

    #-----Key Path-----

    @api.multi
    def get_default_key_path(self, fields):
        return {'key_path': self.env['ir.values'].get_default('voip.settings', 'key_path')}

    @api.multi
    def set_default_key_path(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'key_path', record.key_path)

    #-----Fingerprint-----

    @api.multi
    def get_default_fingerprint(self, fields):
        return {'fingerprint': self.env['ir.values'].get_default('voip.settings', 'fingerprint')}

    @api.multi
    def set_default_fingerprint(self):
        for record in self:
            self.env['ir.values'].set_default('voip.settings', 'fingerprint', record.fingerprint)

    def generate_self_signed_certificate(self):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        cert = crypto.X509()
        cert.get_subject().C = "US" #Country
        cert.get_subject().ST = "Springfield" #State
        cert.get_subject().L = "Evergreen Terrace" #Locality
        cert.get_subject().O = "Simpsons" #Organization
        cert.get_subject().OU = "Homer" #Organization Unit
        cert.get_subject().CN = gethostname() #Common Name
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        home_directory = os.path.expanduser('~')
        cert_path = home_directory + "/cert.crt"
        key_path = home_directory + "/cert.key"
        
        cert_data = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)

        open(cert_path, "wt").write(cert_data)
        open(key_path, "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
        
        self.cert_path = cert_path
        self.key_path = key_path
        
        #Isn't there some library somewhere to generate the fingerprint?
        fingerprint_hex = sha256(cert_data.rstrip()).hexdigest()
        fingerprint_format = ""
        counter = 0
        for char in fingerprint_hex:
            fingerprint_format += char.upper()
            counter += 1
            if counter % 2 == 0:
                fingerprint_format += ":"
        
        self.fingerprint = fingerprint_format[:-1]
        
    def invite_listener(self):
        _logger.error("Invite listen")

        #Kill the existing thread
        #sipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #sipsocket.sendto( "DIE BOT DIE", ("", 5060) )
        
        #Twilio will only send to 5060 which kinda destroys the whole multi db setup
        invite_listener_starter = threading.Thread(target=self.env['voip.account'].invite_listener, args=(5060, 60,))
        invite_listener_starter.start()

        #invite_listener_starter = threading.Thread(target=self.env['voip.account'].invite_listener, args=(5061, 60,))
        #invite_listener_starter.start()
        
    def make_stun_request(self):
        
        #----Compose binding request-----
        send_data = ""
        
        #Message Type (Binding Request)
        send_data += b'\x00\x01'

        #Message Length
        send_data += b'\x00\x00'

        #Magic Cookie (always set to 0x2112A442)
        send_data += b'\x21\x12\xA4\x42'

        #96 bit (12 byte) transaction ID
        send_data += os.urandom(12)
                
        stunsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        
        stunsocket.sendto( send_data, ("stun.voipline.net.au", 3478) )
        stunsocket.settimeout(10)
        try:
            data, addr = stunsocket.recvfrom(1280)
        except Exception as e:
            _logger.error("failed to get stun:" + str(e) )
        
        mapped_port_binary = data[26:28]
        mapped_port = struct.unpack('!H', mapped_port_binary)[0]
     
        mapped_address_binary = data[28:32]
        ip = struct.unpack('BBBB', mapped_address_binary)
        ip = str(ip[0]) + '.' + str(ip[1]) + '.' + str(ip[2]) + '.' + str(ip[3])
        
        return {'ip': ip, 'port': mapped_port}