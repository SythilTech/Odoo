# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp.http import request
import socket
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResUsersVoip(models.Model):

    _inherit = "res.users"

    voip_ringtone = fields.Binary(string="VOIP Ringtone")
    voip_ringtone_filename = fields.Char(string="VOIP Ringtone Filename")

    def create_video_voip_room(self):
        self.create_voip_room("videocall")

    def create_audio_voip_room(self):
        self.create_voip_room("audiocall")

    def create_screensharing_voip_room(self):
        self.create_voip_room("screensharing")

    def create_voip_room(self, mode):

        #The call is created now but the timer doesn't start until the peer to peer connection is successful
        voip_call = request.env['voip.call'].create({'type': 'internal', 'mode': mode})
        
        #Add the current user is the call owner
        voip_call.from_partner_id = self.env.user.partner_id.id

        #Add the selected user as the to partner        
        voip_call.partner_id = self.partner_id.id

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'joined', 'name': self.env.user.partner_id.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.partner_id.id, 'state':'invited', 'name': self.partner_id.name})
        
        notifications = []

        ringtone = "/voip/ringtone/" + str(voip_call.id) + "/" + str(self.id) + ".mp3"
        ring_duration = request.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Complicated code just to get the display name of the mode...
        mode_display = dict(self.env['voip.call'].fields_get(allfields=['mode'])['mode']['selection'])[mode]
        
        #Send notification to callee
        notification = {'call_id': voip_call.id, 'ringtone': ringtone, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming', 'ring_duration': ring_duration, 'mode':mode_display}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.partner_id.id), notification)  

        #Also send one to yourself so we get the countdown
        notification = {'call_id': voip_call.id, 'to_name': self.partner_id.name, 'callee_partner_id': self.partner_id.id, 'direction': 'outgoing', 'ring_duration': ring_duration}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.env.user.partner_id.id), notification)