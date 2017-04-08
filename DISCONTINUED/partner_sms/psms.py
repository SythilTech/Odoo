from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class psms_conf(models.Model):

    _name = "psms.conf"
    
    name = fields.Char(required=True, string='Gateway Name')
    username = fields.Char(required='True', string='API Username')
    password = fields.Char(required='True', string='API Password')
    from_number = fields.Char(required='True', string='From Number')

class psms_compose_multi(models.TransientModel):

    _name = "psms.compose.multi"
    
    sms_gateway = fields.Many2one('psms.conf', required=True, string='Account/Number')
    sms_content = fields.Text('SMS Content')
    
    @api.one
    def send_sms_multi(self):
        for send_to in self._context['active_ids']:
            my_model = self._context['active_model']
            p_mobile = self.env[my_model].search([('id','=',send_to)])[0].mobile
            my_sms = self.env['esms.core'].send_sms(self.sms_gateway.id, p_mobile, self.sms_content, my_model, send_to, 'mobile')


class psms_compose(models.TransientModel):

    _name = "psms.compose"
    
    error_message = fields.Char(readonly=True)
    record_id = fields.Integer()
    model_id = fields.Char()
    sms_gateway = fields.Many2one('psms.conf', required=True, string='Account/Number')
    to_number = fields.Char(required=True, string='To Mobile Number', readonly=True)
    sms_content = fields.Text(string='SMS Content')
    field_id = fields.Char(string='Field Name')

    @api.multi
    def send_entity(self):
        self.ensure_one()
        my_sms = self.env['esms.core'].send_sms(self.sms_gateway.id, self.to_number, self.sms_content, self.model_id, self.record_id, self.field_id)
        if my_sms == "INSUFFICIENT CREDIT":
	    message_return = "Insufficent Credit"
	elif my_sms == "BAD CREDENTIALS":
	    message_return = "Bad Credentials"
	elif my_sms == "FAILED DELIVERY":
	   message_return = "Failed to Deliver"
	elif my_sms == "SUCCESSFUL":
	   message_return = "Successful"
	   
	if message_return != "Successful":
	   return {
	   'type':'ir.actions.act_window',
	   'res_model':'psms.compose',
	   'view_type':'form',
	   'view_mode':'form',
	   'target':'new',
	   'context':{'default_field_id':'mobile','default_to_number':self.to_number,'default_record_id':self.record_id,'default_model_id':self.model_id, 'default_error_message':message_return}
	   }

class esms(models.TransientModel):

   _name = "esms.core"

   fake_field = fields.Char()
   
   def send_sms(self, sms_gateway_id, to_number, sms_content, my_model_name, my_record_id, my_field_name):
       sms_gateway = self.env['psms.conf'].search([('id','=',sms_gateway_id)])
       
       gateway_name = "SMSGLOBAL"
       format_number = to_number
       if " " in format_number: format_number.replace(" ", "")
       if "+" in format_number: format_number = format_number.replace("+", "")
       smsglobal_url = "http://www.smsglobal.com/http-api.php?action=sendsms&user=" + sms_gateway.username + "&password=" + sms_gateway.password + "&from=" + sms_gateway.from_number + "&to=" + format_number + "&text=" + sms_content
       response_string = requests.get(smsglobal_url)
       if response_string.text == "ERROR: 88":
           response_code = "INSUFFICIENT CREDIT"
       elif "ERROR: 40" in response_string.text:
           response_code = "BAD CREDENTIALS"
       elif "ERROR" in response_string.text:
           response_code = "FAILED DELIVERY"
       else:
           response_code = "SUCCESSFUL"
       
       sms_gateway_message_id = response_string.text.split('SMSGlobalMsgID:')[1]
       
       
       my_model = self.env['ir.model'].search([('model','=',my_model_name)])
       my_field = self.env['ir.model.fields'].search([('name','=',my_field_name)])
       if response_code == "SUCCESSFUL":
           psms_history = self.env['psms.history'].create({'field_id':my_field[0].id, 'record_id': my_record_id,'model_id':my_model[0].id,'from_mobile':sms_gateway.from_number,'to_mobile':to_number,'sms_content':sms_content,'status_string':response_string.text, 'gateway_name': gateway_name, 'direction':'O','my_date':datetime.utcnow(), 'status_code':'successful', 'sms_gateway_message_id':sms_gateway_message_id})
       else:
           psms_history = self.env['psms.history'].create({'field_id':my_field[0].id, 'record_id': my_record_id,'model_id':my_model[0].id,'from_mobile':sms_gateway.from_number,'to_mobile':to_number,'sms_content':sms_content,'status_string':response_string.text, 'gateway_name': gateway_name, 'direction':'O','my_date':datetime.utcnow(), 'status_code':'failed', 'sms_gateway_message_id':sms_gateway_message_id})
       
       return response_code
       
class psms_history(models.Model):

    _name = "psms.history"
    
    record_id = fields.Integer(readonly=True, string="Record")
    model_id = fields.Many2one('ir.model', readonly=True, string="Model")
    model_name = fields.Char(string="Model Name", related='model_id.model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', readonly=True, string="Field")
    from_mobile = fields.Char(string="From Mobile Number", readonly=True)
    to_mobile = fields.Char(string="To Mobile Number", readonly=True)
    sms_content = fields.Text(string="SMS Message", readonly=True)
    record_name = fields.Char(string="Record Name", compute="_rec_nam")
    status_string = fields.Char(string="Status Code", readonly=True)
    status_code = fields.Selection((('successful', 'Sent'), ('failed', 'Failed to Send'), ('DELIVRD', 'Delivered'), ('EXPIRED','Timed Out'), ('UNDELIV', 'Undelivered')), string='Status Code', readonly=True)
    gateway_name = fields.Char(string="Gateway Name", readonly=True)
    sms_gateway_message_id = fields.Char(string="SMS Gateway Message ID", readonly=True)
    direction = fields.Selection((("I","INBOUND"),("O","OUTBOUND")), string="Direction", readonly=True)
    my_date = fields.Datetime(string="Date", readonly=True, help="The date and time the sms is received or sent")

    @api.one
    @api.depends('record_id', 'model_id')
    def _rec_nam(self):
        my_record = self.env[self.model_id.model].search([('id','=',self.record_id)])
        self.record_name = my_record.name
        

