# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp.http import request
import socket
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResUsersXMPP(models.Model):

    _inherit = "res.users"

    xmpp_account_id = fields.Many2one('xmpp.account', string="XMPP Account")