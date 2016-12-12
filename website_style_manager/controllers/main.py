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
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
# optional python-slugify import (https://github.com/un33k/python-slugify)
try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None
    
class WebsiteStyleManager(http.Controller):    

    @http.route('/style/load', website=True, type='json', auth="user")
    def style_manager_load(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        html_tags = request.env['website.style.htmltag'].search([])
        
        #I have no idea how multi website works...
        my_website = request.env['website'].browse(0)
                
        my_font_family = request.env['website.style.fontfamily'].search([])
        
        tag_html = ""
        
        #Loop once for the pills
        tag_html += "<ul class=\"nav nav-pills nav-stacked\">\n"
        for html_tag in html_tags:
            tag_html += "<li><a data-toggle=\"pill\" href=\"#" + html_tag.html_tag + "\">" + html_tag.name + "</a></li>\n"
            tag_html += "<div class=\"tab-content\">\n"

            tag_html += "  <div id=\"" + html_tag.html_tag + "\" class=\"tab-pane fade\" style=\"padding:20px;\">\n"

            my_tag = request.env['website.style'].search([('html_tag.html_tag','=',html_tag.html_tag)])

            #Font Family Select Box
            tag_html += "    <b>Font Family: </b><select name=\"" + html_tag.html_tag + "_font_family\">\n"
            for font_family in my_font_family:
                tag_html += "      <option value=\"" + str(font_family.id) + "\" style=\"font-family: '" + font_family.name + "';\""
                
                if len(my_tag) > 0:
                    if font_family.name == my_tag[0].font_family.name:
                        tag_html += " selected=\"selected\"" 
                
                tag_html += ">" + font_family.name + "</option>\n" 

            tag_html += "    </select><br/><br/>\n"

            
            tag_html += "<b>Font Colour: </b> <input type=\"text\" name=\"" + html_tag.html_tag + "_font_color\""
            
            if len(my_tag) > 0:
                tag_html += "value=\"" + my_tag[0].font_color + "\""
                
            tag_html += "/><br/><br/>\n"
            
            tag_html += "<b>Font Size: </b> <input type=\"text\" name=\"" + html_tag.html_tag + "_font_size\""
            
            if len(my_tag) > 0:
                tag_html += " value=\"" + my_tag[0].font_size + "\""
            
            tag_html += "/><br/><br/>\n"            
            
            tag_html += "  </div>\n"

            
            tag_html += "</div>\n"

        tag_html += "</ul>\n"        
        
        return {'html_string': tag_html, 'custom_css': my_website.custom_css}