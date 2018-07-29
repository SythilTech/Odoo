# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp.http import request
import socket
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResUsersVoip(models.Model):

    _inherit = "res.users"

    voip_presence_status = fields.Char(string="Voip Presence Status", help="Used for both Webrtc and SIP")
    last_web_client_activity_datetime = fields.Datetime(string="Last Activity Datetime")
    voip_ringtone = fields.Binary(string="Ringtone")
    voip_account_id = fields.Many2one('voip.account', string="SIP Account")
    voip_ringtone_filename = fields.Char(string="Ringtone Filename")
    voip_missed_call = fields.Binary(string="Missed Call Message")
    voip_missed_call_filename = fields.Char(string="Missed Call Message Filename")