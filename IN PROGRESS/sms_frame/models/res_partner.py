# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerSms(models.Model):

    _inherit = "res.partner"

    sms_opt_out = fields.Boolean(string="SMS Opt Out", help="If true the partner can't be sent mass sms, regular sms is stil fine though")
    
    @api.one
    @api.depends('country_id','mobile')
    def _compute_mobile(self):
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