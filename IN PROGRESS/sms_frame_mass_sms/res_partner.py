from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class res_partner_esms(models.Model):

    _inherit = "res.partner"

    sms_opt_out = fields.Boolean(string="SMS Opt Out", help="If true the partner can't be sent mass sms, regular sms is stil fine though")    
    mobile_e164 = fields.Char(string="Mobile e164", store=True, compute='_calc_e164')

    @api.multi
    def esms_action(self):
        
        if len(self.env.context['active_ids']) > 1:
            mass_sms = self.env['esms.mass.sms'].create({'mass_sms_state':'draft'})
            for rec_id in self.env.context['active_ids']:
                rec = self.browse(rec_id)
                if rec.mobile:
                    mass_sms.selected_records = [(4, rec_id)]                
            
            return {
	                'name': 'Mass SMS Form',
	                'view_type': 'form',
	                'view_mode': 'form',
	                'res_model': 'esms.mass.sms',
	                'res_id': mass_sms.id,
	                'type': 'ir.actions.act_window',
            }
            
        else:
            return {
                 'name': 'Individual SMS Compose',
                 'view_type': 'form',
                 'view_mode': 'form',
                 'res_model': 'esms.compose',
                 'target': 'new',
                 'type': 'ir.actions.act_window',
                 'context': {'default_field_id':'mobile','default_to_number':self.mobile_e164, 'default_record_id':self.env.context['active_id'],'default_model_id':'res.partner'}
            }
    
    @api.one
    @api.depends('country_id','mobile')
    def _calc_e164(self):
        if self.mobile and self.country_id and self.country_id.mobile_prefix:
            if self.mobile.startswith("0"):
                self.mobile_e164 = self.country_id.mobile_prefix + self.mobile[1:]
            elif self.mobile.startswith("+"):
                self.mobile_e164 = self.mobile
            else:
                self.mobile_e164 = self.country_id.mobile_prefix + self.mobile
        else:
            self.mobile_e164 = self.mobile