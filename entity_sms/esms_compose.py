# -*- coding: utf-8 -*
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_compose(models.Model):

    _name = "esms.compose"

    def compute_default_value(self):
        return self.env.user.partner_id.mobile
    
    error_message = fields.Char(readonly=True)
    record_id = fields.Integer()
    model_id = fields.Char()
    sms_gateway = fields.Many2one('esms.accounts', string='SMS Gateway Account')
    from_number = fields.Char(default=compute_default_value, string="From Mobile Number")
    to_number = fields.Char(required=True, string='To Mobile Number', readonly=True)
    sms_content = fields.Text(string='SMS Content')
    file_attachments = fields.One2many('esms.mms', 'partner_id', string="MMS Attachments")
    field_id = fields.Char(string='Field Name')
    template_id = fields.Many2one('esms.templates', string="Template")
    from_mobile = fields.Many2one('esms.verified.numbers', required=True, string="From Mobile")        
    
    @api.onchange('template_id')
    def load_template(self):
        if self.template_id.id != False:
            
            sms_rendered_content = self.env['esms.templates'].render_template(self.template_id.template_body, self.template_id.model_id.model, self.record_id)
            
            self.from_mobile = self.template_id.from_mobile.id
            self.sms_content = sms_rendered_content
            self.sms_gateway = self.template_id.account_gateway.id

    @api.multi
    def send_entity(self):
        self.ensure_one()

        gateway_model = self.from_mobile.account_id.account_gateway.gateway_model_name
        my_sms = self.env[gateway_model].send_message(self.from_mobile.account_id.id, self.from_mobile.mobile_number, self.to_number, self.sms_content.encode('utf-8'), self.model_id, self.record_id, self.field_id)
        
        #use the human readable error message if present
        error_message = ""
        if my_sms.human_read_error != "":
            error_message = my_sms.human_read_error
        else:
            error_message = my_sms.response_string
            
	#display the screen with an error code if the sms/mms was not successfully sent
	if my_sms.delivary_state == "failed":
	   return {
	   'type':'ir.actions.act_window',
	   'res_model':'esms.compose',
	   'view_type':'form',
	   'view_mode':'form',
	   'target':'new',
	   'context':{'default_field_id': self.field_id,'default_sms_gateway': self.sms_gateway.id, 'default_to_number':self.to_number,'default_record_id':self.record_id,'default_model_id':self.model_id, 'default_error_message':error_message}
	   }
	else:
	    
	    my_model = self.env['ir.model'].search([('model','=',self.model_id)])

	    #for single smses we only record succesful sms, failed ones reopen the form with the error message
	    esms_history = self.env['esms.history'].create({'record_id': self.record_id,'model_id':my_model[0].id,'account_id':self.sms_gateway.id,'from_mobile':self.from_number,'to_mobile':self.to_number,'sms_content':self.sms_content,'status_string':my_sms.response_string, 'direction':'O','my_date':datetime.utcnow(), 'status_code':my_sms.delivary_state, 'sms_gateway_message_id':my_sms.message_id, 'gateway_id': self.sms_gateway.account_gateway.id})
	    self.env[self.model_id].search([('id','=', self.record_id)]).message_post(body=self.sms_content, subject="SMS Sent")
        
class esms_mms(models.Model):

    _name = "esms.mms"
    
    partner_id = fields.Many2one('esms.compose')
    mms_attachment = fields.Binary(String="Attachment")
