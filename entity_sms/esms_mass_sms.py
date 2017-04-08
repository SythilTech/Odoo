from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_mass_sms(models.Model):

    _name = "esms.mass.sms"
    
    from_mobile = fields.Many2one('esms.verified.numbers', string="From Mobile", domain="[('mobile_verified','=','True')]")
    selected_records = fields.Many2many('res.partner', string="Selected Records", domain="[('sms_opt_out','=',False),('mobile','!=','')]")
    message_text = fields.Text(string="Message Text")
    total_count = fields.Integer(string="Total", compute="_total_count")
    fail_count = fields.Integer(string="Failed", compute="_fail_count")
    queue_count = fields.Integer(string="Queue", compute="_queue_count")
    sent_count = fields.Integer(string="Sent", compute="_sent_count")
    delivered_count = fields.Integer(string="Received", compute="_delivered_count")
    mass_sms_state = fields.Selection((('draft','Draft'),('sent','Sent')), readonly=True, string="State", default="draft")
    model_object_field = fields.Many2one('ir.model.fields', string="Field", domain="[('model_id.model','=','res.partner'),('ttype','!=','one2many'),('ttype','!=','many2many')]", help="Select target field from the related document model.\nIf it is a relationship field you will be able to select a target field at the destination of the relationship.")
    sub_object = fields.Many2one('ir.model', string='Sub-model', readonly=True, help="When a relationship field is selected as first field, this field shows the document model the relationship goes to.")
    sub_model_object_field = fields.Many2one('ir.model.fields', string='Sub-field', help="When a relationship field is selected as first field, this field lets you select the target field within the destination document model (sub-model).")
    copyvalue = fields.Char(string='Placeholder Expression', help="Final placeholder expression, to be copy-pasted in the desired template field.")

    
    @api.one
    @api.onchange('model_object_field')
    def get_sub_model(self):
        if self.model_object_field.relation:
            self.sub_object = self.env['ir.model'].search([('model','=',self.model_object_field.relation)])[0].id
        else:
            self.sub_object = False
        
    @api.onchange('model_object_field','sub_model_object_field')
    def build_exp(self):
        expression = ''
        if self.model_object_field:
            expression = "${object." + self.model_object_field.name
            if self.sub_model_object_field:
                expression += "." + self.sub_model_object_field.name
            expression += "}"
        self.copyvalue = expression
       
    @api.one
    @api.depends('selected_records')
    def _total_count(self):
        self.total_count = len(self.selected_records)

    @api.one
    def _fail_count(self):
        self.fail_count = self.env['esms.history'].search_count([('mass_sms_id','=',self.id), ('status_code','=','failed')])
        
    @api.one
    def _queue_count(self):
        self.queue_count = self.env['esms.history'].search_count([('mass_sms_id','=',self.id), ('status_code','=','queued')])

    @api.one
    def _sent_count(self):
        self.sent_count = self.env['esms.history'].search_count([('mass_sms_id','=',self.id), ('status_code','=','successful')])

    @api.one
    def _delivered_count(self):
        self.delivered_count = self.env['esms.history'].search_count([('mass_sms_id','=',self.id), ('status_code','=','DELIVRD')])
    
    @api.one
    def send_mass_sms(self):
        self.mass_sms_state = "sent"
        for rec in self.selected_records:
            sms_rendered_content = self.env['esms.templates'].render_template(self.message_text, 'res.partner', rec.id)

            message_final = sms_rendered_content + "\n\nReply STOP to stop receiving sms"
            gateway_model = self.from_mobile.account_id.account_gateway.gateway_model_name
	    #my_sms = self.env[gateway_model].send_message(self.from_mobile.account_id.id, self.from_mobile.mobile_number, rec.mobile_e164, message_final, "esms.mass.sms", self.id, "mobile")
            my_model = self.env['ir.model'].search([('model','=','res.partner')])
            
            #unlike single sms we record down failed attempts to send since mass sms works in a "best try" matter, while single sms works in a "try again" matter.
            #Queue the sms for later sending
            esms_history = self.env['esms.history'].create({'mass_sms_id': self.id, 'record_id': rec.id,'model_id':my_model[0].id,'account_id':self.from_mobile.account_id.id,'from_mobile':self.from_mobile.mobile_number,'to_mobile':rec.mobile_e164,'sms_content':message_final, 'direction':'O','my_date':datetime.utcnow(), 'status_code': 'queued', 'gateway_id': self.from_mobile.account_id.account_gateway.id})
            #esms_history = self.env['esms.history'].create({'mass_sms_id': self.id, 'record_id': rec.id,'model_id':my_model[0].id,'account_id':self.from_mobile.account_id.id,'from_mobile':self.from_mobile.mobile_number,'to_mobile':rec.mobile_e164,'sms_content':message_final,'status_string':my_sms.response_string, 'direction':'O','my_date':datetime.utcnow(), 'status_code':my_sms.delivary_state, 'sms_gateway_message_id':my_sms.message_id, 'gateway_id': self.from_mobile.account_id.account_gateway.id})
            
            #record the message in the communication log
            self.env['res.partner'].browse(rec.id).message_post(body=message_final, subject="Mass SMS Sent")
        
        
    @api.model
    def process_sms_queue(self):
        for queued_sms in self.env['esms.history'].search([('status_code','=','queued')], limit=5):
            rec = self.env[queued_sms.model_id.model].browse(queued_sms.record_id)
            my_sms = self.env[queued_sms.gateway_id.gateway_model_name].send_message(
            queued_sms.mass_sms_id.from_mobile.account_id.id
            , queued_sms.mass_sms_id.from_mobile.mobile_number
            , rec.mobile_e164
            , queued_sms.sms_content
            , "esms.mass.sms"
            , queued_sms.mass_sms_id.id
            , "mobile")
            queued_sms.status_code = my_sms.delivary_state