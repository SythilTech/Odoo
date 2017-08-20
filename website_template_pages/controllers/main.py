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
import requests
import unicodedata
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
# optional python-slugify import (https://github.com/un33k/python-slugify)
try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None
    
class WebsiteTemplatePages(http.Controller):    

    @http.route('/template/pages/sync/client', website=True, type='json', auth="user")
    def website_template_pages_sync_client(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        template_server = request.env['ir.config_parameter'].search([('key','=','website_template_server')])[0].value
        check_date = "2001-01-01 01:01:01"

        response_string = requests.get(template_server + "/template/pages/sync/server?check_date=" + check_date)
        my_json =  json.loads(response_string.text.encode('utf-8'))
        
        for server_template_page in my_json['webpage_templates']:        
            s = ustr(server_template_page['name'])
	    uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
	    slug = re.sub('[\W_]', ' ', uni).strip().lower()
            slug = re.sub('[-\s]+', '-', slug)
            page_name = slug
            template_module = "website"
            page_xmlid = "%s.%s" % (template_module, page_name)
            website_id = request.env.context.get('website_id')
            key = template_module + '.' + page_name
        
            #Create if it doesn't already exist
            if request.env['ir.ui.view'].search_count([('name','=',page_name)]) == 0:
                page = request.env['ir.ui.view'].create({'website_id': website_id, 'key': key, 'arch': server_template_page['arch'], 'name': page_name, 'page': True, 'type': 'qweb', 'xml_id': page_xmlid, 'template_online': True})
        
        page_templates = request.env['ir.ui.view'].search([('template_online','=',True)])
        
        html_string = ""
        for page_template in page_templates:
            html_string += "<div class=\"sythil_page_template\">\n"
            html_string += "    <div class=\"page_template_preview_link\"><a href=\"/template/pages/preview/" + str(page_template.id) + "\" target=\"_blank\">Preview</a></div>\n"
            html_string += "    <div class=\"page_template_title\">" + page_template.name + "</div>\n"
            html_string += "    <div class=\"page_template_glass_overlay\" data-template=\"" + str(page_template.id) + "\"/>\n"            
            html_string += "    <div class=\"sythil_iframe_wrap\"><iframe src=\"/template/pages/preview/" + str(page_template.id) + "\" class=\"sythil_webpage_preview\"/></div>\n"
            html_string += "    <br/>\n"
            html_string += "</div>\n"
        
        return {'html_string': html_string}
    
    @http.route('/template/pages', website=True, type='json', auth="user")
    def website_template_pages_load(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        page_templates = request.env['ir.ui.view'].search([('is_webpage_template','=',True)])
        
        html_string = ""
        for page_template in page_templates:
            html_string += "<div class=\"sythil_page_template\">\n"
            html_string += "    <div class=\"page_template_preview_link\"><a href=\"/template/pages/preview/" + str(page_template.id) + "\" target=\"_blank\">Preview</a></div>\n"
            html_string += "    <div class=\"page_template_title\">" + page_template.name + "</div>\n"
            html_string += "    <div class=\"page_template_glass_overlay\" data-template=\"" + str(page_template.id) + "\"/>\n"            
            html_string += "    <div class=\"sythil_iframe_wrap\"><iframe src=\"/template/pages/preview/" + str(page_template.id) + "\" class=\"sythil_webpage_preview\"/></div>\n"
            html_string += "    <br/>\n"
            html_string += "</div>\n"
        
        return {'html_string': html_string}

    @http.route('/template/pages/preview/<template_id>', website=True, type='http', auth="user")
    def website_template_pages_preview(self, template_id, **kw):
        template = request.env['ir.ui.view'].browse( int(template_id) )
        if template.is_webpage_template or template.template_online:
            return http.request.render(template.id, {})

    @http.route('/template/pages/save', website=True, type='json', auth="user")
    def website_template_pages_save(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        view_id = values['view_id']
        current_view = request.env['ir.ui.view'].search([('key','=',view_id)] )
                
        #Duplicate the current view
        new_view = current_view.copy()
        
        #We need to modify the new page to classify it as a template
        new_view.name = new_view.name + " - Template"
        new_view.is_webpage_template = True

        return {'code': 'good'}

    @http.route('/template/pages/new', website=True, type='json', auth="user")
    def website_template_pages_new(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        page_template = request.env['ir.ui.view'].browse( int(values['template_id']) )
        s = ustr(values['page_name'])
	uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
	slug = re.sub('[\W_]', ' ', uni).strip().lower()
        slug = re.sub('[-\s]+', '-', slug)
        page_name = slug
        template_module = "website"
        page_xmlid = "%s.%s" % (template_module, page_name)
        website_id = request.env.context.get('website_id')
        key = template_module + '.' + page_name
        
        #Create a new view with the content of the page template
        page = request.env['ir.ui.view'].create({'website_id': website_id, 'key': key, 'arch': page_template.arch.replace('website_template_pages.placeholder', page_xmlid), 'name': page_name, 'page': True, 'type': 'qweb', 'xml_id': page_xmlid})
        
        return {'page_name': page_name}