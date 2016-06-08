# -*- coding: utf-8 -*-
import requests
import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json
import openerp
import os
import zipfile,os.path

class AppStoreControllers(http.Controller):

    @http.route('/appstore/module/download', type="json", auth="user")
    def app_store_download(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        app_store = request.env['ir.config_parameter'].get_param('custom_app_store_url')
	module_file = requests.get(app_store + "/apps/modules/download/" + values['module_name'])


        
        home_directory = os.path.expanduser('~')
        mod_name = values['module_name']
        app_directory = home_directory + "/.local/share/Odoo/addons/9.0/" + mod_name + ".zip"
        
        #Save zip to addons folder
        with open(app_directory, 'wb') as handle:
            for block in module_file.iter_content(1024):
	        handle.write(block)

        module_path = home_directory + "/.local/share/Odoo/addons/9.0/" + mod_name
        zip_ref = zipfile.ZipFile(app_directory, 'r')
        zip_ref.extractall(module_path)
        zip_ref.close()
        
        #Update Module List
        request.env['ir.module.module'].update_list()
        
        install_module = request.env['ir.module.module'].search([('name','=',mod_name)])[0]
	install_module.button_immediate_install()
                
        return True