# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp.http import request
import socket
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResUsersVoip(models.Model):

    _inherit = "res.users"

    voip_ringtone = fields.Binary(string="Ringtone")
    voip_ringtone_filename = fields.Char(string="Ringtone Filename")
    voip_missed_call = fields.Binary(string="Missed Call Message")
    voip_missed_call_filename = fields.Char(string="Missed Call Message Filename")

    def create_video_voip_room(self):
        self.create_voip_room("videocall")

    def create_audio_voip_room(self):
        self.create_voip_room("audiocall")

    def create_screensharing_voip_room(self):
        self.create_voip_room("screensharing")

    def create_voip_room(self, mode):

        #Which contraints we used are determined by the starting mode of call
        constraints = {}
        if mode == "videocall":
            constraints = {'audio': True, 'video': True}
        elif mode == "audiocall":
            constraints = {'audio': True}
        elif mode == "screensharing":
            constraints = {'video': {
                    'mediaSource': "screen"
                }
            }

        #Ask for media permission from the caller
        notification = {'mode': mode, 'to_partner_id': self.partner_id.id, 'constraints':  constraints, 'call_type': 'internal'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.permission', self.env.user.partner_id.id), notification)