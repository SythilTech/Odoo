# -*- coding: utf-8 -*-
import base64
import requests
import urllib
import os
from os.path import expanduser
from datetime import datetime
from lxml import html, etree
import logging
_logger = logging.getLogger(__name__)
import zipfile
import json
import io
import csv
import werkzeug.utils
import werkzeug.wrappers

from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class AppsController(http.Controller):

    @http.route('/client/apps', type="http", auth="public", website=True)
    def client_browse_apps(self, **kwargs):
        """Browse all the modules inside Odoo client"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        modules = request.env['module.overview'].search([])
        return http.request.render('app_store.client_app_list', {'modules':modules})

    @http.route('/apps', type="http", auth="public", website=True)
    def browse_apps(self, **kwargs):
        """Browse all the modules"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        modules = request.env['module.overview'].search([])
        return http.request.render('app_store.app_list', {'modules':modules})

    @http.route('/apps/modules/download/<module_name>', type="http", auth="public")
    def app_download(self, module_name, **kwargs):
        """Download the module zip"""

        filename = module_name + ".zip"
        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', "attachment; filename=" + filename ),
        ]

        module = request.env['module.overview'].sudo().search([('name', '=', module_name)])
        module.module_download_count += 1

        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"

        response = werkzeug.wrappers.Response(open(app_directory + "/" + module_name + ".zip", mode="r+b"), headers=headers, direct_passthrough=True)
        return response

    def content_disposition(self, filename):
        filename = ustr(filename)
        
        #escaped = urllib2.quote(filename.encode('utf8'))
        
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

        if module.published == False:
            return "No hack bypassing published"

        module.sudo().module_view_count += 1

        header_string = ""
        for keys,values in request.httprequest.headers.items():
            header_string += keys + ": " + values + "\n"

        ref = ""
        if "Referer" in request.httprequest.headers:
            ref = request.httprequest.headers['Referer']

        request.env['module.overview.store.view'].sudo().create({'mo_id': module.id, 'ref':ref, 'ip': request.httprequest.remote_addr,'header':header_string})

        return http.request.render('app_store.app_page', {'overview':module})

    @http.route('/client/apps/modules/<module_name>', type="http", auth="public", website=True)
    def app_page_client(self, module_name, **kwargs):
        """View all the details about a module"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        module = request.env['module.overview'].search([('name','=',module_name)])

        if module.published == False:
            return "No hack bypassing published"
        
        module.module_view_count += 1

        header_string = ""
        for keys,values in request.httprequest.headers.items():
            header_string += keys + ": " + values + "\n"

        ref = ""
        if "Referer" in request.httprequest.headers:
            ref = request.httprequest.headers['Referer']

        request.env['module.overview.store.view'].create({'mo_id': module.id, 'ref':ref, 'ip': request.httprequest.remote_addr,'header':header_string})

        return http.request.render('app_store.client_app_page', {'overview':module})

    @http.route('/custom/store/updates', type="http", auth="public")
    def custom_app_store_updates(self, **kwargs):
        module_list = []
        for md in request.env['module.overview'].search([]):
            if md.version.startswith("11.0."):
                module_list.append({'name': md.name, 'latest_version': md.version})            
            else:
                #Prefix with 11.0 so we can compare against the installed version
                module_list.append({'name': md.name, 'latest_version': "11.0." + md.version})

        return json.dumps(module_list)