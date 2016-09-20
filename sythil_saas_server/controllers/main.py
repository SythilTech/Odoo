# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
import os
import zipfile
import shutil
import json
import subprocess
from datetime import datetime, timedelta
import tempfile
import StringIO
import requests

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasMultiDB(http.Controller):

    @http.route('/try/package', type="http", auth="public", website=True)
    def saas_package(self, **kw):
        """Webpage that let's a user select a template database / package"""
        template_databases = request.env['saas.template.database'].search([])
        return http.request.render('sythil_saas_server.saas_choose_package', {'template_databases': template_databases})

    @http.route('/template/details/<template_id>', type="http", auth="public", website=True)
    def template_details(self, template_id, **kw):
        """Lists what is inside the template database"""

        template_database = request.env['saas.template.database'].browse( int(template_id) )
        
        #connect to the newly created database
	db = openerp.sql_db.db_connect(template_database.database_name)

        #Create new registry
        registry = openerp.modules.registry.RegistryManager.new(template_database.database_name, False, None, update_module=True)

        page_data_applications = ""
        page_data_builtin = ""
        page_data_community = ""
        groups_string = ""
        
        buildin_modules_list = []
        for buildin_module in request.env['saas.modules.builtin'].search([]):
            buildin_modules_list.append(buildin_module.name)

	#Get a list of all the installed modules
	with closing(db.cursor()) as cr:
	    cr.autocommit(True)     # avoid transaction block
	    
	    #Application list
	    application_modules = registry['ir.module.module'].search(cr, SUPERUSER_ID, [('state','=','installed'), ('application','=',True) ])
	    for installed_module_id in application_modules:
	        installed_module = registry['ir.module.module'].browse(cr, SUPERUSER_ID, installed_module_id)
	        page_data_applications += "<h3>" + installed_module.shortdesc + " (" + installed_module.name + ")</h3>"
	        
	    #Built in modules
	    builtin_modules = registry['ir.module.module'].search(cr, SUPERUSER_ID, [('state','=','installed'), ('application','=',False)])
	    for installed_module_id in builtin_modules:
	        installed_module = registry['ir.module.module'].browse(cr, SUPERUSER_ID, installed_module_id)
	        if installed_module.name in buildin_modules_list:
	            page_data_builtin += "<h3>" + installed_module.shortdesc + " (" + installed_module.name + ")</h3>"
	    
	    #Community Modules
	    community_modules = registry['ir.module.module'].search(cr, SUPERUSER_ID, [('state','=','installed')])
	    for installed_module_id in community_modules:
	        installed_module = registry['ir.module.module'].browse(cr, SUPERUSER_ID, installed_module_id)
	        if installed_module.name not in buildin_modules_list:
	            page_data_community += "<h3><a href=\"https://www.odoo.com/apps/modules/9.0/" + installed_module.name + "\">" + installed_module.shortdesc + " (" + installed_module.name + ")</a></h3>"
	            
	    saas_user_id = registry['ir.model.data'].get_object_reference(cr, SUPERUSER_ID, 'sythil_saas_client', 'saas_user')[1]
            saas_user = registry['res.users'].browse(cr, SUPERUSER_ID, saas_user_id)
            for group in saas_user.groups_id:
                groups_string += "<h3>" + group.display_name + "</h3>\n"

        return http.request.render('sythil_saas_server.template_details', {'page_data_applications': page_data_applications, 'page_data_builtin': page_data_builtin, 'page_data_community':page_data_community, 'template_database': template_database, 'groups_string': groups_string})

    @http.route('/try/details', type="http", auth="public", website=True)
    def saas_info(self, **kw):
        """Webpage for users to enter details about thier saas setup"""

        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value
	    
	template_database = request.env['saas.template.database'].browse(int(values['templatedb']))
        return http.request.render('sythil_saas_server.saas_submit', {'template_database': template_database})

    @http.route('/saas/template/download/<template_id>', type="http", auth="public")
    def saas_template_download(self, template_id, **kw):
        """Transfer the saas database to the SAAS client"""
        template_database = request.env['saas.template.database'].browse( int(template_id) )

        with openerp.tools.osutil.tempdir() as dump_dir:
            db_name = template_database.database_name
            filestore = openerp.tools.config.filestore(db_name)

            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))

            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = openerp.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(self.dump_db_manifest(cr), fh, indent=4)
                    
            cmd = ['pg_dump', '--no-owner']
            cmd.append(db_name)
            cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
            openerp.tools.exec_pg_command(*cmd)
    
            t=tempfile.TemporaryFile()
            openerp.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
            
            headers = [
                ('Content-Type', 'application/octet-stream; charset=binary'),
                ('Content-Disposition', "attachment; filename=template.zip" ),
            ]

            t.seek(0)
            response = werkzeug.wrappers.Response(t, headers=headers, direct_passthrough=True)
            return response

    def dump_db_manifest(self, cr):
        pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': openerp.release.version,
            'version_info': openerp.release.version_info,
            'major_version': openerp.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest
        
    @http.route('/saas/module/download/<module_name>', type="http", auth="public")
    def saas_module_download(self, module_name, **kw):
        """Download the module for the saas client"""

        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value
                
        t = tempfile.TemporaryFile()
        module_directory = openerp.modules.get_module_path(module_name)
        with zipfile.ZipFile(t, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
	    for dirname, subdirs, files in os.walk(module_directory):
                for filename in files:
                    full_path = os.path.join(dirname, filename)
                    zf.write(full_path, os.path.relpath(full_path, module_directory) )
        

        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', "attachment; filename=module.zip" ),
        ]

        t.seek(0)
        response = werkzeug.wrappers.Response(t.read(), headers=headers, direct_passthrough=True)
        return response

    @http.route('/saas/module/requirements', type="http", auth="user")
    def saas_module_requirements(self, **kwargs):
        """Determines which modules are required for the template database to work"""
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
        demo = False
	template_database = request.env['saas.template.database'].browse(int(values["package"]))
	server_url = values['url']

        #connect to the newly created database
	db = openerp.sql_db.db_connect(template_database.database_name)

        #Create new registry
        registry = openerp.modules.registry.RegistryManager.new(template_database.database_name, demo, None, update_module=True)

        installed_module_string = ""
        my_return = []

	#Get a list of installed modules on the template database
	with closing(db.cursor()) as cr:
	    cr.autocommit(True)     # avoid transaction block
	    for installed_module_id in registry['ir.module.module'].search(cr, SUPERUSER_ID, [('state','=','installed')] ):
	        installed_module = registry['ir.module.module'].browse(cr, SUPERUSER_ID, installed_module_id )	        
		my_return.append({"name": installed_module.name, "version":installed_module.installed_version}) 
	        	    
        payload = {'templatedbdata': json.JSONEncoder().encode({"templatedb": template_database.id, "modules":my_return}) }
        response_string = requests.post("http://" + server_url + '/saas/client/load', data=payload)
        
        return json.JSONEncoder().encode({"templatedb": template_database.id, "modules":my_return})
        
    @http.route('/saas/createdb', type="http", auth="public")
    def saas_create_datadb(self, **kwargs):
        """Creates and sets up the new database"""
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	
	email = values["email"]
	password = values["password"]
	company = values["company"]
	system_name = values["company"]
	person_name = values["person_name"]
        demo = False

        #System name comes from company name
        system_name = system_name.replace(" ","")
        system_name = system_name.replace("'","")        
        
        if system_name.isalnum() == False:
            return "Only AlphaNumeric characters allowed"

        #Check if this email has been used to create a SAAS system before
        if request.env['saas.database'].sudo().search_count([('login','=',email)]) > 0:
            return "Email already used to create SAAS system"

	#get the template database
	template_database = request.env['saas.template.database'].browse(int(values["package"]))
	chosen_template = template_database.database_name

        #Create the associated company(res.partner) record
        saas_tag = request.env['ir.model.data'].sudo().get_object('sythil_saas_server', 'saas_client_tag')
        new_company = request.env['res.partner'].sudo().create({'name': company, 'company_type':'company', 'email': email, 'category_id': [(4,saas_tag.id)] })
        new_company.child_ids.sudo().create({'parent_id': new_company.id, 'type':'contact', 'name':person_name, 'email': email, 'category_id': [(4,saas_tag.id)] })
        
	#Add this database to the saas list
	new_saas_database = request.env['saas.database'].create({'name':system_name, 'login': email, 'password': password, 'template_database_id': template_database.id, 'partner_id': new_company.id})

        
        
        #Create the new database from the template database, disconnecting any users that might be using the template database
        db_original_name = chosen_template
        db_name = system_name
        openerp.sql_db.close_db(db_original_name)
        db = openerp.sql_db.db_connect('postgres')        
        with closing(db.cursor()) as cr:
            cr.autocommit(True)     # avoid transaction block
            self._drop_conn(cr, db_original_name)
            
            #Check if the database already exists
	    cr.execute("SELECT datname FROM pg_database WHERE datname = %s",(db_name,))
	    if cr.fetchall():
	        return "Database already exists"
	        
            cr.execute("""CREATE DATABASE "%s" ENCODING 'unicode' TEMPLATE "%s" """ % (db_name, db_original_name))

        from_fs = openerp.tools.config.filestore(db_original_name)
        to_fs = openerp.tools.config.filestore(db_name)
        
        if os.path.exists(from_fs) and not os.path.exists(to_fs):
            shutil.copytree(from_fs, to_fs)

        #connect to the newly created database
	db = openerp.sql_db.db_connect(db_name)

        #Create new registry
        registry = openerp.modules.registry.RegistryManager.new(system_name, demo, None, update_module=True)

	#Update the saas user's name, email, login and password
	with closing(db.cursor()) as cr:
	    cr.autocommit(True)     # avoid transaction block
	    saas_user = registry['ir.model.data'].get_object(cr, SUPERUSER_ID, 'sythil_saas_client', 'saas_user')
	    saas_user.write({'name':person_name, 'email':email, 'login':email, 'password':password})
	    saas_company = registry['ir.model.data'].get_object(cr, SUPERUSER_ID, 'base', 'main_company')
	    saas_company.name = company
        
        #Auto login the user
        #request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	#request.session.authenticate(system_name, email, password)
        
        if request.env['ir.config_parameter'].get_param('saas_system_redirect') == "db_filter":
            return werkzeug.utils.redirect("http://" + request.httprequest.host + "/web?db=" + system_name)
        else:
            return werkzeug.utils.redirect("http://" + system_name + "." + request.httprequest.host )
        
    def _drop_conn(self, cr, db_name):
        # Try to terminate all other connections that might prevent
        # dropping the database
        try:
            # PostgreSQL 9.2 renamed pg_stat_activity.procpid to pid:
            # http://www.postgresql.org/docs/9.2/static/release-9-2.html#AEN110389
            pid_col = 'pid' if cr._cnx.server_version >= 90200 else 'procpid'
    
            cr.execute("""SELECT pg_terminate_backend(%(pid_col)s)
                          FROM pg_stat_activity
                          WHERE datname = %%s AND
                                %(pid_col)s != pg_backend_pid()""" % {'pid_col': pid_col},
                       (db_name,))
        except Exception:
            pass