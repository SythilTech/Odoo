# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import api, fields, models

class MarketingCampaignSms(models.Model):

    _inherit = "marketing.campaign.activity"
    
    type = fields.Selection(selection_add=[('sms','SMS')])
    sms_template_id = fields.Many2one('sms.template', string="SMS Template")
    
    @api.model
    def _process_wi_sms(self, activity, workitem):

        sms_template = self.env['sms.template'].browse(activity.sms_template_id.id)
        rendered_sms_to = self.env['sms.template'].render_template(sms_template.sms_to, workitem.object_id.model, workitem.res_id)
        rendered_sms_template_body = self.env['sms.template'].render_template(sms_template.template_body, workitem.object_id.model, workitem.res_id)

	my_sms = self.env[sms_template.from_mobile_verified_id.account_id.account_gateway_id.gateway_model_name].send_message(sms_template.from_mobile_verified_id.account_id.id, sms_template.from_mobile_verified_id.mobile_number, rendered_sms_to, rendered_sms_template_body, workitem.object_id.model, workitem.res_id)
            
        #unlike single sms we record down failed attempts to send since campaign sms works in a "best try" matter, while single sms works in a "try again" matter.
        self.env['sms.message'].create({'record_id': workitem.res_id,'model_id':workitem.object_id.id,'account_id':sms_template.from_mobile_verified_id.account_id.id,'from_mobile':sms_template.from_mobile,'to_mobile':rendered_sms_to,'sms_content':rendered_sms_template_body,'status_string':my_sms.response_string, 'direction':'O','message_date':datetime.utcnow(), 'status_code':my_sms.delivary_state, 'sms_gateway_message_id':my_sms.message_id, 'gateway_id': sms_template.from_mobile_verified_id.account_id.account_gateway_id.id})
            
        #record the message in the communication log
        self.env[workitem.object_id.model].browse(workitem.res_id).message_post(body=rendered_sms_template_body, subject="Marketing Campaign SMS")
