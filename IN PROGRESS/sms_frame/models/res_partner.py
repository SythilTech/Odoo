from openerp import models, fields, api

class ResPartnerSms(models.Model):

    _inherit = "res.partner"

    sms_opt_out = fields.Boolean(string="SMS Opt Out", help="If true the partner can't be sent mass sms, regular sms is stil fine though")    
    
    @api.multi
    def sms_action(self):
        return {
             'name': 'Individual SMS Compose',
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'sms.compose',
             'target': 'new',
             'type': 'ir.actions.act_window',
             'context': {'default_field_id':'mobile','default_to_number':self.mobile, 'default_record_id':self.env.context['active_id'],'default_model_id':'res.partner'}
            }
    
    @api.one
    @api.depends('country_id','mobile')
    def _calc_e164(self):
        if self.mobile and self.country_id and self.country_id.mobile_prefix:
            if self.mobile.startswith("0"):
                self.mobile = self.country_id.mobile_prefix + self.mobile[1:]
            elif self.mobile.startswith("+"):
                self.mobile = self.mobile
            else:
                self.mobile = self.country_id.mobile_prefix + self.mobile
        else:
            self.mobile = self.mobile