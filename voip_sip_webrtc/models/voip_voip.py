# -*- coding: utf-8 -*-
from openerp.http import request
import socket
import threading
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, registry

class VoipVoip(models.Model):

    _name = "voip.voip"
    _description = "Voip Functions"

    @api.model
    def sip_read_message(self, data):
        sip_dict = {}
        for line in data.split("\n"):
            sip_key = line.split(":")[0]
            sip_value = line[len(sip_key) + 2:]
            sip_dict[sip_key] = sip_value

        #Get from SIP address
        from_sip = sip_dict['From']
        start = from_sip.index( "sip:" ) + 4
        end = from_sip.index( ";", start )
        sip_dict['from_sip'] = from_sip[start:end].replace(">","").strip()

        #Get to SIP address
        sip_dict['to_sip'] = sip_dict['To'].split("sip:")[1].strip()
            
        return sip_dict
        
    @api.model
    def start_sip_call(self, to_partner):
        #Ask for media permission from the caller
        mode = "audiocall"
        constraints = {'audio': True}
        notification = {'mode': mode, 'to_partner_id': to_partner, 'constraints':  constraints, 'call_type': 'external'}
        self.env['bus.bus'].sendone((self._cr.dbname, 'voip.sip', self.env.user.partner_id.id), notification)
                    
    @api.model
    def start_incoming_sip_call(self, sip_invite, addr, sip_tag):

        sip_dict = self.sip_read_message(sip_invite)

        #Find the from partner
        from_partner_id = self.env['res.partner'].sudo().search([('sip_address', '=', sip_dict['from_sip'] )])

        #Find the to partner
        to_partner_id = self.env['res.partner'].sudo().search([('sip_address', '=', sip_dict['to_sip'] )])
            
        #SIP INVITE will continously send, only allow one call from this person at a time, as a future feature if multiple people call they are allowed to join the call with permission
        if self.env['voip.call'].search_count([('status', '=', 'pending'), ('from_partner_id', '=', from_partner_id.id), ('partner_id', '=', to_partner_id.id)]) < 50:

            _logger.error("INVITE: " + str(sip_invite) )
            _logger.error("from partner:" + str(from_partner_id.name) )
            _logger.error("to partner:" + str(to_partner_id.name) )
            
            #The call is created now so we can update it as a missed / rejected call or accepted, the timer for the call starts after being accepted though
            voip_call = self.env['voip.call'].create({'type': 'external', 'direction': 'incoming', 'sip_tag': sip_tag})

            ringtone = "/voip/ringtone/" + str(voip_call.id) + ".mp3"
            ring_duration = self.env['ir.default'].get('voip.settings', 'ring_duration')
            
            #Assign the caller and callee partner
            voip_call.from_partner_id = from_partner_id
            voip_call.partner_id = to_partner_id

            #Add the to calle to the client list
            self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': to_partner_id.id, 'state':'joined', 'name': to_partner_id.name})

            #Also add the external partner to the list but assume we already have media access, the long polling will be ignored since the from is external to the system
            self.env['voip.call.client'].sudo().create({'vc_id':voip_call.id, 'partner_id': from_partner_id.id, 'state':'media_access', 'name': from_partner_id.name, 'sip_invite': sip_invite, 'sip_addr_host': addr[0], 'sip_addr_port': addr[1] })

            #Send notification to callee
            notification = {'voip_call_id': voip_call.id, 'ringtone': ringtone, 'ring_duration': ring_duration, 'from_name': from_partner_id.name, 'caller_partner_id': from_partner_id.id, 'direction': 'incoming', 'mode': "audiocall"}
            self.env['bus.bus'].sendone((self._cr.dbname, 'voip.notification', to_partner_id.id), notification)
        
        #Have to manually commit the new cursor?
        self.env.cr.commit()