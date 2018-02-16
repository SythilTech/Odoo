# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import sleekxmpp
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
import ssl
import sys
from odoo import api, fields, models, registry
from odoo.exceptions import UserError

class XMPPMessageCompose(models.TransientModel):

    _inherit = "voip.message.compose"

    xmpp_account_id = fields.Many2one('xmpp.account', string="XMPP Account")

    def _send_xmpp_message(self):

        logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
        
        _logger.error("XMPP Message")

        if sys.version_info < (3, 0):
            reload(sys)
            sys.setdefaultencoding('utf8')
    
        xmpp_account = self.xmpp_account_id
        
        if xmpp_account == False:
            raise UserError("Please set XMPP account for this user first")
            
        _logger.error(xmpp_account.address)
        
        xmpp = XMPPClientMessageCompose(xmpp_account.address, xmpp_account.password, self.partner_id.xmpp_address, self.message, self.partner_id.id, self)
 
        if xmpp.connect():
            _logger.error("Can connect")
            xmpp.process(block=True)
            
            self.partner_id.message_post(body=self.message)
        else:
            _logger.error("Unable to connect")
        
class XMPPClientMessageCompose(ClientXMPP):

    def __init__(self, jid, password, recipient, msg, partner_id, ood_env):
        ClientXMPP.__init__(self, jid, password)

        self.recipient = recipient
        self.msg = msg
        self.partner_id = partner_id
        self.ood_env = ood_env
        
        self.add_event_handler('session_start', self.xmpp_start)
        self.add_event_handler('message', self.xmpp_message)

    def xmpp_start(self, event):
        _logger.error("XMPP Session Start")
        self.send_presence()
        self.get_roster()
         
        self.send_message(mto=self.recipient, mbody=self.msg, mtype='chat')
         
        self.disconnect(wait=True)
                
    def xmpp_message(self, msg):
        _logger.error(msg['body'])
