from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class EsmsHistory(models.Model):

    _name = "esms.history"
    _order = "my_date desc"
    
    record_id = fields.Integer(readonly=True, string="Record")
    account_id = fields.Many2one('esms.accounts', readonly=True, string="SMS Account")
    gateway_id = fields.Many2one('esms.gateways', readonly=True, string="SMS Gateway")
    mass_sms_id = fields.Many2one('esms.mass.sms', readonly=True, string="Mass SMS")
    model_id = fields.Many2one('ir.model', readonly=True, string="Model")
    model_name = fields.Char(string="Model Name", related='model_id.model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', readonly=True, string="Field")
    from_mobile = fields.Char(string="From Mobile", readonly=True)
    to_mobile = fields.Char(string="To Mobile", readonly=True)
    sms_content = fields.Text(string="SMS Message", readonly=True)
    record_name = fields.Char(string="Record Name", compute="_rec_nam")
    status_string = fields.Char(string="Response String", readonly=True)
    status_code = fields.Selection((('RECEIVED','Received'), ('failed', 'Failed to Send'), ('queued', 'Queued'), ('successful', 'Sent'), ('DELIVRD', 'Delivered'), ('EXPIRED','Timed Out'), ('UNDELIV', 'Undelivered')), string='Delivary State', readonly=True)
    sms_gateway_message_id = fields.Char(string="SMS Gateway Message ID", readonly=True)
    direction = fields.Selection((("I","INBOUND"),("O","OUTBOUND")), string="Direction", readonly=True)
    my_date = fields.Datetime(string="Send/Receive Date", readonly=True, help="The date and time the sms is received or sent")
    delivary_error_string = fields.Text(string="Delivary Error")

    @api.one
    @api.depends('to_mobile')
    def _rec_nam(self):
        if self.model_id != False and self.record_id != False:
            my_record_count = self.env[self.model_id.model].search_count([('id','=',self.record_id)])
            if my_record_count > 0:
                my_record = self.env[self.model_id.model].search([('id','=',self.record_id)])
                self.record_name = my_record.name
            else:
                self.record_name = self.to_mobile
                
                
    @api.model
    def create(self, values):
        new_rec = super(EsmsHistory, self).create(values)
        
        autoreslist = self.env['esms.autoresponse'].search([('from_mobile','=',new_rec.to_mobile), ('keyword','=ilike',new_rec.sms_content)])
	if len(autoreslist) > 0 and new_rec.direction == 'I':
	    autores = autoreslist[0]
	    my_sms = self.env[new_rec.account_id.account_gateway.gateway_model_name].send_message(new_rec.account_id.id, new_rec.to_mobile, new_rec.from_mobile, autores.sms_content, new_rec.model_id.model, new_rec.record_id, new_rec.field_id.name)
	                
	    esms_history = self.env['esms.history'].create({'record_id': new_rec.record_id,'model_id':new_rec.model_id.id,'account_id':new_rec.account_id.id,'from_mobile':new_rec.from_mobile,'to_mobile':new_rec.to_mobile,'sms_content':autores.sms_content,'status_string':my_sms.response_string, 'direction':'O','my_date':datetime.utcnow(), 'status_code':my_sms.delivary_state, 'sms_gateway_message_id':my_sms.message_id, 'gateway_id': new_rec.account_id.account_gateway.id})
            
            #record the message in the communication log
            if new_rec.model_id.model == "res.partner": 
                self.env['res.partner'].browse(new_rec.record_id).message_post(body=autores.sms_content, subject="SMS Auto Response")

	
	if new_rec.sms_content == 'STOP' and new_rec.direction == 'I' and new_rec.model_name == 'res.partner':
	    for rec in self.env['res.partner'].search([('id','=',new_rec.record_id)]):
	        rec.sms_opt_out = True
	        #Send opt out response
                self.env[new_rec.account_id.account_gateway.gateway_model_name].send_message(new_rec.account_id.id, new_rec.to_mobile, new_rec.from_mobile, 'You have been unsubscribed from mass sms', new_rec.model_id.model, new_rec.record_id, new_rec.field_id.name)