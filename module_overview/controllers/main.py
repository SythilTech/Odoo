# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import requests
import urllib
import os
from os.path import expanduser
from datetime import datetime
from lxml import html, etree
import logging
_logger = logging.getLogger(__name__)
import zipfile

class ModuleOverView(http.Controller):

    @http.route('/module/overview', type="http", auth="public", website=True)
    def module_picker(self, **kwargs):
        """Gives an overview of what is inside a module"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if "version" not in values or "name" not in values:
            return http.request.render('module_overview.pick_module', {})
                
        #Get the download url from the app store page
        #module_url = "https://apps.openerp.com/apps/modules/" + values['version'] + "/" + values['name'] + "/"
        #page = requests.get(module_url)        
        #root = html.fromstring(page.content)
        #my_elements = root.xpath("//a[@id='dlbtn']")
	#if len(my_elements) != 0:
	#    download_url = my_elements[0].attrib['href']
	
	#Download the file
	#download_url = "https://apps.odoo.com/loempia/download/website_blog_mgmt/9.0.1.0.0/2Jyn9JzWRtSRItWuTOTV8C.zip?deps"
	#home = expanduser("~")
	#name, hdrs = urllib.urlretrieve(download_url, home + "/" + values['name'] + ".zip")

        module_overview = request.env['module.overview'].create({'name': values['name']})

        name = "/odoo/sms_frame.zip"
        myzipfile = zipfile.ZipFile(name)
        overview_string = ""
        for file_name in myzipfile.namelist():
            filename, file_extension = os.path.splitext(file_name)
            zippy = myzipfile.open(file_name)
            if file_extension == ".py":
                _logger.error("not supported")
                #self._read_py(zippy.read(), module_overview.id)
            elif  file_extension == ".xml":
                self._read_xml(zippy.read(), module_overview.id)
                
                
	
        return http.request.render('module_overview.pick_module', {'overview':module_overview})
                
    def _read_py(self, file_content, m_id):        
        return ""
        
    def _read_xml(self, file_content, m_id):
        return_string = ""
        root = etree.fromstring(file_content)
        insert_records = root.xpath('//record')
        for rec in insert_records:
    	    record_id = rec.attrib['id']
    	    record_name = rec.xpath("//field[@name='name']")[0].text
    	    model_name = rec.xpath("//field[@name='model']")[0].text
    	    model_exist = request.env['module.overview.model'].search([('name','=',model_name )])
    	    model = ""
    	    
    	    #if this is the first time encountering model, create it.
    	    if len(model_exist) == 0:
    	        model = request.env['module.overview.model'].create({'mo_id': m_id, 'name': model_name})
    	    else:
    	        model = model_exist[0]
    	        
    	    #add this view to this model
    	    request.env['module.overview.model.view'].create({'model_id': model.id, 'name': record_name, 'x_id': record_id})