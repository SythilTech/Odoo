from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class sms_response():
     response_string = ""
     response_code = ""

class smsgateway_core(models.Model):

    _name = "esms.smsgateway"

    api_url = fields.Char(string='API URL')

    def send_sms(self, sms_gateway_id, to_number, sms_content, my_model_name, my_record_id, my_field_name):
        sms_account = self.env['esms.accounts'].search([('id','=',sms_gateway_id)])

        format_number = to_number
        if " " in format_number: format_number.replace(" ", "")
        if "+" in format_number: format_number = format_number.replace("+", "")
        smsgateway_url = "http://smsgateway.ca/sendsms.aspx?CellNumber=" + str(format_number) + "&MessageBody=" + str(sms_content) + "&AccountKey=" + str(sms_account.smsgateway_accountkey)
        response_string = requests.get(smsgateway_url)

        response_code = ""
	status_code = ""
        if "Message queued successfully" in response_string.text:
	    status_code = "successful"
	    response_code = "SUCCESSFUL"
	else:
	    status_code = "failed"
	    response_code = "FAILED DELIVERY"

        my_model = self.env['ir.model'].search([('model','=',my_model_name)])
        my_field = self.env['ir.model.fields'].search([('name','=',my_field_name)])

        esms_history = self.env['esms.history'].create({'field_id':my_field[0].id, 'record_id': my_record_id,'model_id':my_model[0].id,'account_id':sms_account.id,'from_mobile':'','to_mobile':to_number,'sms_content':sms_content,'status_string':response_string.text, 'direction':'O','my_date':datetime.utcnow(), 'status_code':status_code})

        my_sms_response = sms_response()
        my_sms_response.response_string = response_string.text
        my_sms_response.response_code = response_code

        return my_sms_response

class smsgateway_conf(models.Model):

    _inherit = "esms.accounts"

    smsgateway_accountkey = fields.Char(string='API AccountKey')