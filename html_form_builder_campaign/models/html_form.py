# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class HtmlFormCampaign(models.Model):

    _inherit = "html.form"
    
    campaign_form = fields.Boolean(string="Campaign Form")
    campaign_id = fields.Many2one('marketing.campaign', required=True, string="Campaign")
    
    @api.one
    @api.onchange('campaign_form')
    def _onchange_campaign_form(self):
        if self.campaign_form:
            self.submit_url =  request.httprequest.host_url + "form/campaign"