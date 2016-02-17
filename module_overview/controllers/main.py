# -*- coding: utf-8 -*-
import base64
import openerp.http as http
from openerp.http import request
import requests
import urllib
import StringIO
import os
from os.path import expanduser
from datetime import datetime
from lxml import html, etree
import logging
_logger = logging.getLogger(__name__)
import zipfile
import io
import csv

class ModuleOverView(http.Controller):

    @http.route('/module/overview', type="http", auth="public", website=True, csrf=False)
    def module_picker(self, **kwargs):
        """Gives an overview of what is inside a module"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
                
        #Get the download url from the app store page
        #module_url = "https://apps.openerp.com/apps/modules/" + values['version'] + "/" + values['name'] + "/"
        #page = requests.get(module_url)        
        #root = html.fromstring(page.content)
        #my_elements = root.xpath("//a[@id='dlbtn']")
	#if len(my_elements) != 0:
	#    download_url = my_elements[0].attrib['href']
	
	#Download the file
	#home = expanduser("~")
	#name, hdrs = urllib.urlretrieve(download_url, home + "/" + values['name'] + ".zip")

        #Use the cached copy of the module
        if 'module' in values:
            module_overview = request.env['module.overview'].search([('name','=', values['module'] )])[0]
            return http.request.render('module_overview.pick_module', {'overview':module_overview})

        if "upload" not in values:
            return http.request.render('module_overview.pick_module', {})
            
        upload = values['upload']
        module_name = os.path.splitext(upload.filename)[0]

        #Delete the existing module record
        delete_module = request.env['module.overview'].search([('name','=',module_name)])
        
        if delete_module:
            delete_module[0].unlink()
        
        module_overview = request.env['module.overview'].create({'name': module_name})

        myzipfile = zipfile.ZipFile(io.BytesIO(field_value.read()))
        overview_string = ""
        for file_name in myzipfile.namelist():
            filename, file_extension = os.path.splitext(file_name)
            zippy = myzipfile.open(file_name)
            if file_extension == ".py":
                _logger.error("not supported")
                #self._read_py(zippy.read(), module_overview.id)
            elif file_extension == ".xml":
                self._read_xml(zippy.read(), module_overview.id)
            elif file_extension == ".csv":
                self._read_csv(filename, zippy.read(), module_overview.id)
                
                
	
        return http.request.render('module_overview.pick_module', {'overview':module_overview})
                
    def _read_py(self, file_content, m_id):        
        return ""
        
    def _read_csv(self, file_name, file_content, m_id):        
        if "ir.model.access":
            rownum = 0
            reader = csv.reader(StringIO.StringIO(file_content), delimiter=',')
            header = []
            for row in reader:
                row_dict = {'mo_id': m_id}
                # Save header row.
                if rownum == 0:
                    header = row
                else:
                    colnum = 0
                    for col in row:
                         #map the csv header columns to the fields 
                         if header[colnum] == "id":
                             row_dict['x_id'] = col
                         elif header[colnum] == "model_id:id":
                             row_dict['model'] = col                         
                         elif header[colnum] == "group_id:id":
                             row_dict['group'] = col                          
                         elif header[colnum] == "perm_read":
                             row_dict['perm_read'] = bool(int(col))                          
                         elif header[colnum] == "perm_write":
                             row_dict['perm_write'] = bool(int(col))                          
                         elif header[colnum] == "perm_create":
                             row_dict['perm_create'] = bool(int(col))                          
                         elif header[colnum] == "perm_unlink":
                             row_dict['perm_unlink'] = bool(int(col))                       
                         else:                         
                             row_dict[header[colnum]] = col
                         
                         colnum += 1
                
                    #Create a access rule record using the premade dictionary from the csv
                    request.env['module.overview.access'].create(row_dict)
                rownum += 1
       
    def _read_xml(self, file_content, m_id):
        return_string = ""
        root = etree.fromstring(file_content)
        
        insert_menu = root.xpath('//menuitem')
        for menu in insert_menu:
            menu_dict = {'mo_id': m_id}
            menu_dict['x_id'] = menu.attrib['id']

            if 'name' in menu.attrib:
                menu_dict['name'] = menu.attrib['name']

            if 'parent' in menu.attrib:
                menu_dict['parent'] = menu.attrib['parent']

            request.env['module.overview.menu'].create(menu_dict)
        
        insert_records = root.xpath('//record')
        for rec in insert_records:
    	    record_id = rec.attrib['id']
    	    
    	    #If it's a view
    	    if rec.attrib['model'] == "ir.ui.view":
    	    
    	        record_name = rec.find(".//field[@name='name']").text
    	        model_name = rec.find(".//field[@name='model']").text
    	        model_exist = request.env['module.overview.model'].search([('name','=',model_name),('mo_id','=',m_id) ])
    	        model = ""
    	    
    	        #if this is the first time encountering model, create it.
    	        if len(model_exist) == 0:
    	            model = request.env['module.overview.model'].create({'mo_id': m_id, 'name': model_name})
    	        else:
    	            model = model_exist[0]
    	        
    	        #add this view to this model
    	        request.env['module.overview.model.view'].create({'model_id': model.id, 'name': record_name, 'x_id': record_id})