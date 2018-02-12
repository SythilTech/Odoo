# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models

class ResPartnerYeastar(models.Model):

    _inherit = "res.partner"
    
    mobile_without_spaces = fields.Char(string="Mobile Compare", compute="_compute_mobile_without_spaces", store="True")
    
    @api.one
    @api.depends('mobile')
    def _compute_mobile_without_spaces(self):
        if self.mobile:
            self.mobile_without_spaces = self.mobile.replace(" ", "").replace(u'\xa0', "").replace("-","")