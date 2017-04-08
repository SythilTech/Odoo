from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class wanal_requests(models.Model):

    _name = "wanal.request"
    _order = "write_date desc"
    
    ref_url = fields.Char(string=" Reference URL", readonly='True')
    target_url = fields.Char(string="Target URL", readonly='True')
    ip = fields.Char(string="IP", readonly='True')
    user_agent = fields.Char(string="User Agent", readonly="True")
    keyword = fields.Char(string="Keyword", readonly="True")
    header = fields.Text(string="Header String", readonly="True")
    
    def web_track(self, request):
        ref = ""
        header_string = ""
        keyword = ""
        
        #search_engine_list = ["google.com.au","google.com"]
        
        for keys,values in request.httprequest.headers.items():
	    header_string += keys + ": " + values + "\n"
    
        if "Referer" in request.httprequest.headers:
            ref = request.httprequest.headers['Referer']
        
        request.env['wanal.request'].create({'ref_url':ref,'target_url':request.httprequest.url, 'keyword': keyword, 'ip': request.httprequest.remote_addr,'user_agent':'noidea','header':header_string})
