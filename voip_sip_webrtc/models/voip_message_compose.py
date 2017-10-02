# -*- coding: utf-8 -*-
import socket
import threading
import logging
_logger = logging.getLogger(__name__)
from lxml import etree
import re

from openerp import api, fields, models

class VoipMessageCompose(models.TransientModel):

    _name = "voip.message.compose"

    type = fields.Char(string="Message Type")
    partner_id = fields.Many2one('res.partner', string="Partner")
    message = fields.Text(string="Message")

    def xmpp_listener(self, to_address):
                
        _logger.error("Start XMMP Listening")

        try:
            account = to_address.split("@")[0]
            domain = to_address.split("@")[1]
            _logger.error(domain)

            xmpp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            xmpp_socket.connect( ('216.189.159.196', 5222) )
            #xmpp_socket.connect((domain, 5222))
            
            send_data = ""
            send_data += '<?xml version="1.0"?>'
            #send_data += '<stream:stream xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" to="jabberzac.org" version="1.0">'
            send_data += '<stream:stream xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" to="' + str(domain) + '" version="1.0">'

            xmpp_socket.send(send_data)
            rec_data = xmpp_socket.recv(1024)
            
            _logger.error(rec_data)
            
            stream_id = re.findall(r"id='(.*?)'", rec_data)[0]
            
            send_data = '<starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls"/>'
            xmpp_socket.send(send_data)
            
            rec_data = xmpp_socket.recv(1024)
            _logger.error(rec_data)
            
            if "proceed" in rec_data:
                _logger.error("We did it!!!")

            xmpp_socket.close             

        except Exception as e:
            _logger.error(e)

        
    def send_message(self):
        _logger.error("Send Message")


        method = '_send_%s_message' % (self.type,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

        action()