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

class VoipSettings(models.Model):

    _name = "voip.settings"
    _inherit = 'res.config.settings'
            
    missed_call_action = fields.Selection([('nothing', 'Nothing')], string="Missed Call Action", help="What action is taken when the call is missed")
    ringtone_id = fields.Many2one('voip.ringtone', string="Ringtone")
    ringtone = fields.Binary(string="Default Ringtone")
    ringtone_filename = fields.Char("Ringtone Filename")
    ring_duration = fields.Integer(string="Ring Duration (Seconds)")
    message_bank_duration = fields.Integer(string="Message Bank Duration (Seconds)", help="The time before message bank automatically hangs up")
    sip_running = fields.Boolean(string="SIP Running")
    server_ip = fields.Char(string="Public IP")
    cert_path = fields.Char(string="Cert Path", help="Used by message bank")
    key_path = fields.Char(string="Key Path", help="Used by message bank")
    fingerprint = fields.Char(string="Fingerprint", help="Used by message bank")
    sip_listening = False

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

    def sip_server(self):
        _logger.error("Start SIP Listening")
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.bind(('', 5060));

        sip_tag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))

        sip_listening = True
        while sip_listening:
            data, addr = serversocket.recvfrom(2048)

            if not data: 
                break
        
            _logger.error(data)

            #Read the body as a dictionary
            sip_dict = {}
            for line in data.split("\n"):
                sip_key = line.split(":")[0]
                sip_value = line[len(sip_key) + 2:]
                sip_dict[sip_key] = sip_value
        
            
            if data.startswith("OPTIONS"):
                _logger.error("options")
            elif data.startswith("REGISTER"):
                _logger.error("register")
            elif data.startswith("ACK"):
                _logger.error("ack")
            elif data.startswith("INVITE"):
                _logger.error("invite")
                _logger.error(data)

                #Send 180 Ringing
                reply = ""
                reply += "SIP/2.0 180 Ringing\r\n"
                reply += "Via: " + sip_dict['Via'].strip() + "\r\n"                
                reply += "From: " + sip_dict['From'].strip() + "\r\n"
                reply += "To: " + sip_dict['To'].strip() + ";tag=" + str(sip_tag) + "\r\n"
                reply += "Contact: " + sip_dict['Contact'].strip() + "\r\n"
                reply += "Call-ID: " + sip_dict['Call-ID'].strip() + "\r\n"
                reply += "CSeq: " + sip_dict['CSeq'].strip() + "\r\n"
                reply += "Content-Length: 0\r\n"
                #_logger.error("180 RINGING: " + reply )
                _logger.error(addr)
                serversocket.sendto(reply, addr)

                with api.Environment.manage():
                    # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
                    new_cr = self.pool.cursor()
                    self = self.with_env(self.env(cr=new_cr))
                    self.env['voip.voip'].start_incoming_sip_call(data, addr, sip_tag)
                    self._cr.close()
        
        #Close the socket
        _logger.error("SIP Shutdown")
        serversocket.shutdown(socket.SHUT_RDWR)
        serversocket.close()
        
    def start_sip_server(self):
        #Start a new thread so you don't block the main Odoo thread
        sip_socket_thread = threading.Thread(target=self.sip_server, args=())
        sip_socket_thread.start()
        
    def stop_sip_server(self):
        _logger.error("Stop SIP Server")
        sip_listening = False
        self.sip_running = False