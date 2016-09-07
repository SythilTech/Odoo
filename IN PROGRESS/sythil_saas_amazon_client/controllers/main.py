# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
import os
import shutil
import subprocess
from datetime import datetime, timedelta
import json
import urllib2
import requests
import zipfile
import StringIO

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasAmazonClient(http.Controller):

    @http.route('/saas/client/load', type='http', auth="none")
    def saas_client_amazon_load(self, **kw):
        """Downloads modules and template database from saas server"""
        
        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value
    
        templatedbdata = values['templatedbdata']
        
        request.env.cr.execute("SELECT COUNT(*) as num_database FROM pg_database;")
        num_databases = request.env.cr.fetchone()[0]
        home_directory = os.path.expanduser('~')
        
        #Only import if their is no databases other then the 3 templates
        if num_databases >= 3:
            #Get a list of modules in this instance
            mod_list = openerp.modules.get_modules()
            #mod_path = openerp.modules.get_module_path(i)
            #info = openerp.modules.load_information_from_description_file(i)
            
            #Download the missing modules
            template_data = json.loads(templatedbdata)
            for template_module in template_data['modules']:
                 if template_module['name'] not in mod_list:
                     _logger.error(template_module['name'])

            app_directory = home_directory + "/.local/share/Odoo/addons/9.0/" + "crm" + ".zip"
            r = requests.get("http://192.168.56.109:8069/saas/template/download/1", stream=True)
            
            _logger.error( len(r.content) )
            
            localFile = open(app_directory, "wb")

            with open(app_directory, 'wb') as f:
                for data in r.iter_content():
                    localFile.write(data)
            
            #z = zipfile.ZipFile(app_directory)
            #new_module_directory = app_directory + "crm"
            #os.makedirs(new_module_directory)
            #z.extractall(new_module_directory)
                
        return "Hi"