# -*- coding: utf-8 -*-
from datetime import datetime
import uuid
import urlparse
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class MarketingCampaignSurvey(models.Model):

    _inherit = "marketing.campaign.activity"
    
    type = fields.Selection(selection_add=[('survey','Survey')])
    survey_id = fields.Many2one('marketing.survey.template', string="Survey")
    
    @api.model
    def _process_wi_survey(self, activity, workitem):

        survey_template = self.env['marketing.survey.template'].browse(activity.survey_id.id)
       	
       	partner = self.env['res.partner'].browse( int(workitem.res_id) )
       	
       	#Create Token
       	token = uuid.uuid4().__str__()
	self.env['survey.user_input'].create({'survey_id': activity.survey_id.survey_id.id, 'date_create': datetime.now(), 'type': 'link', 'state': 'new', 'token': token, 'partner_id': partner.id, 'email': partner.email})

        #Create URL
        url = activity.survey_id.survey_id.public_url
        #url = urlparse.urlparse(url).path[1:]  # dirty hack to avoid incorrect urls
        url = url + '/' + token

       	#Build Email
       	survey_template.partner_to = workitem.res_id
       	survey_template.subject = activity.survey_id.subject

        values = {
            'model': None,
            'res_id': None,
            'subject': activity.survey_id.subject,
            'body': activity.survey_id.body.replace("__URL__", url),
            'body_html': activity.survey_id.body.replace("__URL__", url),
            'parent_id': None,
            'email_from': activity.survey_id.email_from or None,
            'auto_delete': False,
        }
            
        values['recipient_ids'] = [(4, partner.id)]
                
            
        
        mail_mail_obj = self.env['mail.mail']
        mail_id = mail_mail_obj.create(values)
        mail_mail_obj.send([mail_id])                        
