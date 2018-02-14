from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class SmsMass(models.Model):

    _name = "sms.mass"
    
    from_mobile = fields.Many2one('sms.number', string="From Mobile")
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
    stop_message = fields.Char(string="STOP message", default="reply STOP to unsubscribe", required="True")
    
    @api.onchange('model_object_field')
    def _onchange_model_object_field(self):
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
       
    @api.depends('selected_records')
    @api.one
    def _total_count(self):
        self.total_count = len(self.selected_records)

    @api.one
    def _fail_count(self):
        self.fail_count = self.env['sms.message'].search_count([('mass_sms_id','=',self.id), ('status_code','=','failed')])

    @api.one
    def _queue_count(self):
        self.queue_count = self.env['sms.message'].search_count([('mass_sms_id','=',self.id), ('status_code','=','queued')])

    @api.one
    def _sent_count(self):
        self.sent_count = self.env['sms.message'].search_count([('mass_sms_id','=',self.id), ('status_code','=','successful')])

    @api.one
    def _delivered_count(self):
        self.delivered_count = self.env['sms.message'].search_count([('mass_sms_id','=',self.id), ('status_code','=','DELIVRD')])
    
    def send_mass_sms(self):
        self.mass_sms_state = "sent"
        for rec in self.selected_records:

            sms_rendered_content = self.env['sms.template'].render_template(self.message_text, 'res.partner', rec.id)

            sms_rendered_content += "\n\n" + self.stop_message
            
            #Queue the SMS message and send them out at the limit
            queued_sms = self.env['sms.message'].create({'record_id': rec.id,'model_id': self.env.ref('base.model_res_partner').id,'account_id':self.from_mobile.account_id.id,'from_mobile':self.from_mobile.mobile_number,'to_mobile':rec.mobile,'sms_content':sms_rendered_content, 'direction':'O','message_date':datetime.utcnow(), 'status_code': 'queued', 'mass_sms_id': self.id})            

            #Turn the queue manager on
            sms_queue = self.env['ir.model.data'].get_object('sms_frame', 'sms_queue_check')
            sms_queue.sudo().write({'active': True})