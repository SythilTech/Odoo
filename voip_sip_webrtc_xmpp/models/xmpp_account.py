# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class XMPPAccount(models.Model):

    _name = "xmpp.account"
    _rec_name = "address"

    address = fields.Char(string="Address")
    password = fields.Char(string="Password")