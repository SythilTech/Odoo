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

class VoipAccount(models.Model):

    _name = "voip.account"
    _rec_name = "address"

    type = fields.Selection([('sip', 'SIP'), ('xmpp', 'XMPP')], default="sip", string="Account type")
    address = fields.Char(string="SIP Address")
    password = fields.Char(string="SIP Password")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username")
    domain = fields.Char(string="Domain")
    outbound_proxy = fields.Char(string="Outbound Proxy")
    verified = fields.Boolean(string="Verified")
    
    @api.onchange('address')
    def _onchange_address(self):
        if self.address:
            if "@" in self.address:
                self.username = self.address.split("@")[0]
                self.domain = self.address.split("@")[1]
        
    def send_register(self):
  
        local_ip = self.env['ir.values'].get_default('voip.settings', 'server_ip')

        register_string = ""
        register_string += "REGISTER sip:" + self.domain + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
        register_string += "Max-Forwards: 70\r\n"
        register_string += "Contact: <sip:" + self.username + "@" + local_ip + ":5060>\r\n" #:54443 XOR port mapping?
        register_string += 'To: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">\r\n"
        register_string += 'From: "' + self.env.user.partner_id.name + '"<sip:' + self.address + ">;tag=903df0a\r\n"
        register_string += "Call-ID: " + self.env.cr.dbname + "-account-" + str(self.id) + "\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        register_string += "Expires: 3600\r\n"
        register_string += "Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n"
        register_string += "User-Agent: Sythil Tech Voip Client 1.0.0\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"

        _logger.error("REGISTER: " + register_string)
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.sendto(register_string, (self.outbound_proxy, 5060) )