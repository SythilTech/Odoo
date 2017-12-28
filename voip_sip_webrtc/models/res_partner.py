# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.exceptions import UserError

class ResPartnerVoip(models.Model):

    _inherit = "res.partner"
    
    sip_address  = fields.Char(string="SIP Address")
    xmpp_address  = fields.Char(string="XMPP Address")
    
    @api.onchange('country_id','mobile')
    def _onchange_mobile(self):
        """Tries to convert a local number to e.164 format based on the partners country, don't change if already in e164 format"""
        if self.mobile:                    
                
            if self.country_id and self.country_id.phone_code:
                if self.mobile.startswith("0"):
                    self.mobile = "+" + str(self.country_id.phone_code) + self.mobile[1:].replace(" ","")
                elif self.mobile.startswith("+"):
                    self.mobile = self.mobile.replace(" ","")
                else:
                    self.mobile = "+" + str(self.country_id.phone_code) + self.mobile.replace(" ","")
            else:
                self.mobile = self.mobile.replace(" ","")
                
                
    @api.multi
    def sip_action(self):
        self.ensure_one()

        my_context = {'default_type': 'sip', 'default_model':'res.partner', 'default_record_id':self.id, 'default_to_address': self.sip_address}        
        
        #Use the first SIP account you find
        default_voip_account = self.env['voip.account'].search([])
        if default_voip_account:
            my_context['default_sip_account_id'] = default_voip_account[0].id
        else:
            raise UserError("No SIP accounts found, can not send message")
           
        return {
            'name': 'SIP Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'voip.message.compose',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': my_context
         }
