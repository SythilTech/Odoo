# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import api, fields, models

class MarketingCampaignSms(models.Model):

    _inherit = "marketing.campaign.activity"
    
    action_type = fields.Selection(selection_add=[('sms','SMS')])
    sms_template_id = fields.Many2one('sms.template', string="SMS Template")
    
    @api.multi
    def _process_wi_sms(self, workitem):
        self.ensure_one()

        sms_template = self.env['sms.template'].browse(workitem.activity_id.sms_template_id.id)
        rendered_sms_to = self.env['sms.template'].render_template(sms_template.sms_to, workitem.object_id.model, workitem.res_id)
        rendered_sms_template_body = self.env['sms.template'].render_template(sms_template.template_body, workitem.object_id.model, workitem.res_id)

        #Queue the SMS message and send them out at the limit
        queued_sms = self.env['sms.message'].create({'record_id': workitem.res_id,'model_id':workitem.object_id.id,'account_id':sms_template.from_mobile_verified_id.account_id.id,'from_mobile':sms_template.from_mobile,'to_mobile':rendered_sms_to,'sms_content':rendered_sms_template_body, 'direction':'O','message_date':datetime.utcnow(), 'status_code': 'queued'})            

        #Also create the MMS attachment
        if sms_template.media_id:
            self.env['ir.attachment'].sudo().create({'name': 'mms ' + str(queued_sms.id), 'type': 'binary', 'datas': sms_template.media_id, 'public': True, 'res_model': 'sms.message', 'res_id': queued_sms.id})

        #Turn the queue manager on
        self.env['ir.model.data'].get_object('sms_frame', 'sms_queue_check').active = True