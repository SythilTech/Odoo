import openerp.http as http
import openerp
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class HtmlFormControllerActionEmail(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    def _html_action_campaign_signup(self, submit_action, history_data, values):
        
        #Add the new partner to a campaign
        for act in submit_action.campaign_campaign_id.activity_ids:
            if act.start:
                wi = request.env['marketing.campaign.workitem'].sudo().create({'campaign_id': submit_action.campaign_campaign_id.id, 'activity_id': act.id, 'res_id': history_data.record_id})
                wi.process()
                #request.env['mail.mail'].process_email_queue()
