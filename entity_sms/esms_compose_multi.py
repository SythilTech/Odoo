from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_compose_multi(models.TransientModel):

    _name = "esms.compose.multi"
    
    sms_gateway = fields.Many2one('esms.accounts', required=True, string='Account/Number')
    sms_content = fields.Text('SMS Content')
    
    @api.one
    def send_sms_multi(self):
        for send_to in self._context['active_ids']:
            my_model = self._context['active_model']
            p_mobile = self.env[my_model].search([('id','=',send_to)])[0].mobile
	    gateway_model = self.sms_gateway.account_gateway.gateway_model_name
            my_sms = self.env[gateway_model].send_sms(self.sms_gateway.id, p_mobile, self.sms_content, my_model, send_to, 'mobile')
