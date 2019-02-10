# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class CrmLeadSms(models.Model):

    _inherit = "crm.lead"

    @api.multi
    def sms_action(self):
        self.ensure_one()

        default_mobile = self.env['sms.number'].search([])[0]

        return {
            'name': 'SMS Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sms.compose',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_from_mobile_id': default_mobile.id,'default_to_number':self.mobile, 'default_record_id':self.id,'default_model':'crm.lead'}
         }

    def e164_convert(self, phone_code, mobile):
        if mobile:
            if phone_code:
                if mobile.startswith("0"):
                    return "+" + str(phone_code) + mobile[1:].replace(" ","")
                elif mobile.startswith("+"):
                    return mobile.replace(" ","")
                else:
                    return "+" + str(phone_code) + mobile.replace(" ","")
            else:
                return mobile.replace(" ","")

    @api.model
    def create(self, vals):
        if 'country_id' in vals and 'mobile' in vals:
            phone_code = self.env['res.country'].browse(vals['country_id']).phone_code
            vals['mobile'] = self.e164_convert(phone_code, vals['mobile'])
        return super(CrmLeadSms, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'country_id' in vals and 'mobile' in vals:
            phone_code = self.env['res.country'].browse(vals['country_id']).phone_code
            vals['mobile'] = self.e164_convert(phone_code, vals['mobile'])
        if 'country_id' in vals and 'mobile' not in vals:
            phone_code = self.env['res.country'].browse(vals['country_id']).phone_code
            vals['mobile'] = self.e164_convert(phone_code, self.mobile)
        if 'country_id' not in vals and 'mobile' in vals:
            vals['mobile'] = self.e164_convert(self.country_id.phone_code, vals['mobile'])
        return super(CrmLeadSms, self).write(vals)