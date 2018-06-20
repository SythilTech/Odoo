# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartnerTwilioVoip(models.Model):

    _inherit = "res.partner"
        
    @api.multi
    def twilio_mobile_action(self):
        self.ensure_one()

        my_context = {'default_to_number': self.mobile, 'default_record_model': 'res.partner', 'default_record_id': self.id, 'default_partner_id': self.id}
        
        #Use the first number you find
        default_number = self.env['voip.number'].search([])
        if default_number:
            my_context['default_from_number'] = default_number[0].id
        else:
            raise UserError("No numbers found, can not make call")
           
        return {
            'name': 'Voip Call Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'voip.call.wizard',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': my_context
         }

class ResUsersTwilioVoip(models.Model):

    _inherit = "res.users"

    call_routing_ids = fields.Many2many('voip.number', string="Call Routing")
    twilio_client_name = fields.Char(string="Twilio Client Name")
    
    def update_twilio_client_name(self, twilio_identity):
        self.twilio_client_name = twilio_identity
        
    def get_call_details(self, conn):
        twilio_from_mobile = conn['parameters']['From']
        call_from_partner = self.env['res.partner'].sudo().search([('mobile','=',conn['parameters']['From'])])
        caller_partner_id = False
        
        if call_from_partner:
            from_name = call_from_partner.name + " (" + twilio_from_mobile + ")"
            caller_partner_id = call_from_partner.id
        else:
            from_name = twilio_from_mobile

        ringtone = "/voip/ringtone.mp3"
        ring_duration = self.env['ir.default'].get('voip.settings', 'ring_duration')
        
        return {'from_name': from_name, 'caller_partner_id': caller_partner_id, 'ringtone': ringtone, 'ring_duration': ring_duration}