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
    
class WebsiteStyleManager(http.Controller):    

    @http.route('/style/custom.css', website=True, type='http', auth="public")
    def style_custom(self, **kw):
        styles = request.website.custom_css
        return request.make_response(styles, [('Content-Type', 'text/css')])

    @http.route('/style/save', type="json", auth="user", website=True)
    def style_save(self, **kw):
            

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        request.website.custom_css = values['css']
                     
        return {'css_string': values['css']}
        
    @http.route('/style/load', type="json", auth="user", website=True)
    def style_load(self, **kw):
            
        css_string = request.website.custom_css
                     
        return {'css_string': css_string}