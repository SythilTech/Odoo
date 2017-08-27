# -*- coding: utf-8 -*-
import socket
import logging
_logger = logging.getLogger(__name__)
from openerp.http import request

from openerp import api, fields, models

class VoipAccount(models.Model):

    _name = "voip.account"
    _rec_name = "address"

    address = fields.Char(string="SIP Address")
    password = fields.Char(string="SIP Password")
    auth_username = fields.Char(string="Auth Username")
    username = fields.Char(string="Username")
    domain = fields.Char(string="Domain")
    outbound_proxy = fields.Char(string="Outbound Proxy")
    
    @api.onchange('address')
    def _onchange_address(self):
        if self.address:
            if "@" in self.address:
                self.username = self.address.split("@")[0]
                self.domain = self.address.split("@")[1]
        
    def send_register(self):
        local_ip = request.httprequest.headers.environ['HTTP_HOST'].split(":")[0]

        register_string = ""
        register_string += "REGISTER sip:" + self.outbound_proxy + " SIP/2.0\r\n"
        register_string += "Via: SIP/2.0/UDP " + local_ip + "\r\n"
        register_string += "From: <sip:" + request.env.user.partner_id.sip_address + ">;tag=903df0a\r\n"
        register_string += "To: <sip:" + request.env.user.partner_id.sip_address + ">\r\n"
        register_string += "Call-ID: " + "17320\r\n"
        register_string += "CSeq: 1 REGISTER\r\n"
        register_string += "Expires: 3600\r\n"
        register_string += "Contact: " + request.env.user.partner_id.sip_address + " <sip:" + self.username + "@" + self.local_ip + ":5060>\r\n"
        register_string += "Content-Length: 0\r\n"
        register_string += "\r\n"
        
        proxy_ip = self.outbound_proxy
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.sendto(register_string, (proxy_ip, 5070) )

        _logger.error("REGISTER: " + register_string)
    