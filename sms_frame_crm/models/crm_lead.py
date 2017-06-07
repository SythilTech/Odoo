# -*- coding: utf-8 -*-
from openerp import api, fields, models

class CrmLeadSms(models.Model):

    _inherit = "crm.lead"
    
    @api.onchange('country_id','mobile')
    def _onchange_mobile(self):
        """Tries to convert a local number to e.164 format based on the partners country, don't change if already in e164 format"""
        if self.mobile and self.country_id and self.country_id.mobile_prefix:
            if self.mobile.startswith("0"):
                self.mobile = self.country_id.mobile_prefix + self.mobile[1:]
            elif self.mobile.startswith("+"):
                self.mobile = self.mobile
            else:
                self.mobile = self.country_id.mobile_prefix + self.mobile
        else:
            self.mobile = self.mobile