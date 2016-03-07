# -*- coding: utf-8 -*-
import base64
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
import werkzeug.utils
import werkzeug.wrappers
import urllib2

from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class AppsController(http.Controller):

    @http.route('/apps', type="http", auth="public", website=True)
    def browse_apps(self, **kwargs):
        """Browse all the modules"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
                
        modules = request.env['module.overview'].search([])
        return http.request.render('app_store.app_list', {'modules':modules})

    @http.route('/apps/modules/download/<module_name>', type="http", auth="public", website=True)
    def app_download(self, module_name, **kwargs):
        """Download the module zip"""
        filename = str(module_name) + ".zip"
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', "attachment; filename=" + filename ),
        ]
            
            
        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"
        
        response = werkzeug.wrappers.Response(file(app_directory + "/" + module_name + ".zip"), headers=headers, direct_passthrough=True)
        return response        
        
    def content_disposition(self, filename):
        filename = ustr(filename)
        escaped = urllib2.quote(filename.encode('utf8'))
        browser = request.httprequest.user_agent.browser
        version = int((request.httprequest.user_agent.version or '0').split('.')[0])
        if browser == 'msie' and version < 9:
            return "attachment; filename=%s" % escaped
        elif browser == 'safari' and version < 537:
            return u"attachment; filename=%s" % filename.encode('ascii', 'replace')
        else:
            return "attachment; filename*=UTF-8''%s" % escaped
        
    @http.route('/apps/modules/<module_name>', type="http", auth="public", website=True)
    def app_page(self, module_name, **kwargs):
        """View all the details about a module"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
                
        module = request.env['module.overview'].search([('name','=',module_name)])
        return http.request.render('app_store.app_page', {'overview':module})