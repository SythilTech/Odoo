import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)
import werkzeug

class MyController(http.Controller):

    @http.route('/wanal/test',type="http", auth="public")
    def wanal_test(self, **kwargs):
        
        request.env['wanal.request'].web_track(request)
        
        return "test page"
    