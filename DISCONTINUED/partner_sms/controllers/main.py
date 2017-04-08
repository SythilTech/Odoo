import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    @http.route('/sms/receipt',type="http", auth="public")
    def sms_receipt(self, **kwargs):
        _logger.error("read re")
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
            
        gateway_name = "SMSGLOBAL"
        
        attach_obj = request.registry['psms.history']
	rs = attach_obj.search(request.cr, SUPERUSER_ID, [('gateway_name','=',gateway_name), ('sms_gateway_message_id','=',values['msgid'])], limit=1)
	sms_message = attach_obj.browse(request.cr, SUPERUSER_ID, rs)
        
        _logger.error(values['msgid'])
        _logger.error(values['dlrstatus'])
        _logger.error(values['dlr_err'])
        
        sms_message.status_code = values['dlrstatus']
        sms_message.status_string = values['dlr_err']
        
        return "OK"