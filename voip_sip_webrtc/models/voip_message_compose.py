# -*- coding: utf-8 -*-
import socket
import threading
import logging
_logger = logging.getLogger(__name__)

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

            xmpp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            xmpp_socket.connect( ('216.189.159.196', 5222) )
            #xmpp_socket.connect((domain, 5222))
            
            send_data = ""
            send_data += '<?xml version="1.0"?>'
            send_data += '<stream:stream xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" to="jabberzac.org" version="1.0">'
            #send_data += '<stream:stream xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" to="' + str(domain) + '" version="1.0">'

            _logger.error("Before Send")        
            xmpp_socket.send(send_data)
            _logger.error("After Send")

            _logger.error( xmpp_socket.recv(1024) )
            xmpp_socket.close             

        except Exception as e:
            _logger.error(e)

        
    def send_message(self):
        _logger.error("Send Message")

        to_address = self.partner_id.xmpp_address
        xmpp_listener_starter = threading.Thread(target=self.xmpp_listener, args=(to_address,))
        xmpp_listener_starter.start()        