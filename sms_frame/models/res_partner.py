# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerSms(models.Model):

    _inherit = "res.partner"

    @api.multi
    def sms_action(self):
        self.ensure_one()
        
        default_mobile = self.env['sms.number'].search([])[0]
        
        _logger.error(default_mobile.id)
        
        return {
            'name': 'SMS Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sms.compose',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_from_mobile_id': default_mobile.id,'default_to_number':self.mobile, 'default_record_id':self.id,'default_model':'res.partner'}
         }
        
    
    
    @api.onchange('country_id','mobile')
    def _onchange_mobile(self):
        """Tries to convert a local number to e.164 format based on the partners country, don't change if already in e164 format"""
        if self.mobile:                    
            
            if self.country_id and self.country_id.mobile_prefix:
                if self.mobile.startswith("0"):
                    self.mobile = self.country_id.mobile_prefix + self.mobile[1:].replace(" ","")
                elif self.mobile.startswith("+"):
                    self.mobile = self.mobile.replace(" ","")
                else:
                    self.mobile = self.country_id.mobile_prefix + self.mobile.replace(" ","")
            else:
                self.mobile = self.mobile.replace(" ","")