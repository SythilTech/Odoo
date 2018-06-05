# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.exceptions import UserError

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
