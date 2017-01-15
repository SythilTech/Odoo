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

        #The call is created now so we can update it as a missed / rejected call or accepted, the timer for the call starts after being accepted though
        voip_call = request.env['voip.call'].create({'type': 'internal'})
        
        #Add the current user is the call owner
        voip_call.from_partner_id = self.env.user.partner_id.id

        #Add the selected user as the to partner        
        voip_call.partner_id = self.partner_id.id

        #Also add both partners to the client list
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.env.user.partner_id.id, 'state':'joined', 'name': self.env.user.partner_id.name})
        self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': self.partner_id.id, 'state':'invited', 'name': self.partner_id.name})
        
        notifications = []

        rintones = request.env['voip.ringtone'].search([])
        ringtone = "/voip_sip_webrtc/static/src/audio/ringtone.mp3"
        if len(rintones) > 0:
            ringtone = "/voip/ringtone/1/ringtone.mp3"
        
        #Send notification to callee
        notification = {'call_id': voip_call.id, 'ringtone': ringtone, 'from_name': self.env.user.partner_id.name, 'caller_partner_id': self.env.user.partner_id.id, 'direction': 'incoming'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.partner_id.id), notification)  

        #Also send one to yourself so we get the countdown
        notification = {'call_id': voip_call.id, 'to_name': self.partner_id.name, 'callee_partner_id': self.partner_id.id, 'direction': 'outgoing'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', self.env.user.partner_id.id), notification)

        return "Hi"
        #return {
        #    'type': 'ir.actions.act_url',
        #    'target': 'new',
        #    'url': "/voip/window?call=" + str(voip_call.id)
        #}
