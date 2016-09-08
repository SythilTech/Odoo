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
import base64
import tempfile

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasAmazonClient(http.Controller):

    @http.route('/saas/client/test', type='http', auth="none")
    def saas_client_amazon_test(self, **kw):
        #Now download the template database
        r = requests.get("http://sythiltech.com.au/saas/template/download/1", stream=True)
        copy = True
        data = base64.b64encode(r.content)
        openerp.service.db.exp_restore("test3425", data, copy)

        return "Test 3425"

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
            
            #Download the missing modules
            template_data = json.loads(templatedbdata)
            for template_module in template_data['modules']:
                 if template_module['name'] not in mod_list:
                     r = requests.get("http://sythiltech.com.au/saas/module/download/" + template_module['name'], stream=True)
                     z = zipfile.ZipFile(StringIO.StringIO(r.content))
                     os.makedirs(home_directory + "/.local/share/Odoo/addons/9.0/" + template_module['name'])
                     app_directory = home_directory + "/.local/share/Odoo/addons/9.0/" + template_module['name']
                     z.extractall(app_directory)
                     
            #Now download the template database
            r = requests.get("http://sythiltech.com.au/saas/template/download/" + template_data['templatedb'], stream=True)
            data = base64.b64encode(r.content)
            openerp.service.db.exp_restore(template_data['templatedb'], data, True)

        return "Hi"