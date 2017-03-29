# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp.http import request
import socket

from openerp import api, fields, models

class ResUsersVoip(models.Model):

    _inherit = "res.users"
        
    @api.multi
    def create_voip_room(self):
        self.ensure_one()

        #The call is created now but the timer doesn't start until the peer to peer connection is successful
        voip_call = request.env['voip.call'].create({'type': 'internal'})
        
        #Add the current user is the call owner
        voip_call.from_partner_id = self.env.user.partner_id.id

        #Add the selected user as the to partner        
        voip_call.partner_id = self.partner_id.id

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'joined', 'name': self.env.user.partner_id.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.partner_id.id, 'state':'invited', 'name': self.partner_id.name})
        
        notifications = []

        ringtone = "/voip/ringtone/ringtone.mp3"
        
        ring_duration = request.env['ir.values'].get_default('voip.settings', 'ring_duration')
        
        #Send notification to callee
        notification = {'call_id': voip_call.id, 'ringtone': ringtone, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming', 'ring_duration': ring_duration}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.partner_id.id), notification)  

        #Also send one to yourself so we get the countdown
        notification = {'call_id': voip_call.id, 'to_name': self.partner_id.name, 'callee_partner_id': self.partner_id.id, 'direction': 'outgoing', 'ring_duration': ring_duration}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.env.user.partner_id.id), notification)

        return "Hi"
        
