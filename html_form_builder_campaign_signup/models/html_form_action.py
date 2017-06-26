# -*- coding: utf-8 -*-
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class HtmlFormActionCampaign(models.Model):

    _inherit = "html.form.action"
    
    campaign_campaign_id = fields.Many2one('marketing.campaign', string="Campaign", help="The campaign to sign the user up to after completing the form")
    
    @api.onchange('campaign_campaign_id')
    def _onchange_settings_description_campaign(self):
        if self.campaign_campaign_id:
            self.settings_description = "Campaign: " + self.campaign_campaign_id.name
