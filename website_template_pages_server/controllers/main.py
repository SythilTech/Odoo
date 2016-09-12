# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import re
import json
import openerp
import unicodedata
import json
    
class WebsiteTemplatePagesServer(http.Controller):    
    
    @http.route('/template/pages/sync/server', website=True, type='http', auth="public", cors='*')
    def website_template_pages_sync_server(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        check_date = values['check_date']
        
        page_templates = request.env['ir.ui.view'].search([('is_webpage_template_server','=',True), ('__last_update','>',check_date) ])
        
        my_return = []

	#Get a list of installed modules on the template database
	for page_template in page_templates:
	    my_return.append({"name": page_template.name, "arch":page_template.arch}) 
	    
        return json.JSONEncoder().encode({"webpage_templates":my_return})