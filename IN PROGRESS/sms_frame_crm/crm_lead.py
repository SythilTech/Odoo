from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class crm_lead_esms(models.Model):

    _inherit = "crm.lead"
    
    mobile_e164 = fields.Char(string="Mobile e164", store=True, compute='_calc_e164')

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