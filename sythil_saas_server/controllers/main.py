# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
import os
import zipfile
import shutil
import string
import random
import json
import subprocess
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import tempfile
import StringIO
import requests
import odoo
from odoo import api

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID, tools

class SaasMultiDB(http.Controller):

    @http.route('/saas/portal', type="http", auth="user", website=True)
    def saas_portal(self, **kw):
        """Displays a list of databases owned by the current user"""
        user_databases = request.env['saas.database'].search([('user_id','=',request.env.user.id)])
        payment_methods = request.env['payment.token'].search([('partner_id','=',request.env.user.partner_id.id)])

        return http.request.render('sythil_saas_server.saas_portal', {'user_databases': user_databases, 'payment_methods': payment_methods})

    @http.route('/saas/portal/domains', type="http", auth="user", website=True)
    def saas_portal_domains(self, **kw):
        """Displays a list of domains owned by the current user"""
        user_domains = request.env['saas.database.domain'].search([('database_id.user_id','=',request.env.user.id)])
        return http.request.render('sythil_saas_server.saas_portal_domain_list', {'user_domains': user_domains})

    #@http.route('/saas/portal/backup', type="http", auth="user", website=True)
    #def saas_portal_backup(self, **kw):
    #    """Backs up the database only if they own it"""

    #    values = {}
#	for field_name, field_value in kw.items():
#	    values[field_name] = field_value
#
#        user_database = request.env['saas.database'].search([('user_id','=',request.env.user.id), ('id','=', int(values['db']) )])
#        
#        if len(user_database) == 0:
#            return "Hack attempt detected!!!"
#        elif len(user_database) == 1:
#
#            with openerp.tools.osutil.tempdir() as dump_dir:
#                db_name = user_database.name
#                filestore = openerp.tools.config.filestore(db_name)
#
#                if os.path.exists(filestore):
#                    shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
#
#                with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
#                    db = openerp.sql_db.db_connect(db_name)
#                    with db.cursor() as cr:
#                        json.dump(self.dump_db_manifest(cr), fh, indent=4)
#                    
#                cmd = ['pg_dump', '--no-owner']
#                cmd.append(db_name)
#                cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
#                openerp.tools.exec_pg_command(*cmd)
#    
#                t=tempfile.TemporaryFile()
#                openerp.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
#            
#                headers = [
#                    ('Content-Type', 'application/octet-stream; charset=binary'),
#                    ('Content-Disposition', "attachment; filename=backup.zip" ),
#                ]
#
#                t.seek(0)
#                response = werkzeug.wrappers.Response(t, headers=headers, direct_passthrough=True)
#                return response

    @http.route('/try/package', type="http", auth="public", website=True)
    def saas_package(self, **kw):
        """Webpage that let's a user select a template database / package"""
        template_databases = request.env['saas.template.database'].search([])
        return http.request.render('sythil_saas_server.saas_choose_package', {'template_databases': template_databases})

    @http.route('/saas/login/<db_name>', type="http", auth="user")
    def saas_login_process(self, db_name, **kw):

        saas_database = request.env['saas.database'].search([('name','=',db_name), ('partner_id','=',request.env.user.partner_id.id)])

        if saas_database.state == "trial":
            trial_expiration_date = datetime.strptime(saas_database.trial_expiration, tools.DEFAULT_SERVER_DATETIME_FORMAT)

            if datetime.now() > trial_expiration_date:
                return "Trial has exired"
        
        elif saas_database.state == "canceled":
            return "Your subscription has been canceled, please resubscribe to continue using the software"        

        #request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	#request.session.authenticate(saas_database.name, saas_database.login, saas_database.password)

        return werkzeug.utils.redirect(saas_database.access_url)

    @http.route('/saas/unsubscribe', type="http", auth="user")
    def saas_unsubscribe_process(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value

        database_name = values['database']
        user_database = request.env['saas.database'].search([('name','=',database_name), ('partner_id','=', request.env.user.partner_id.id)])

        user_database.sudo().state = "canceled"
        user_database.sudo().next_payment_date = ""
        user_database.sudo().payment_method_id = ""

        #Connect to the saas database and update the subscription status
	db = openerp.sql_db.db_connect(user_database.name)

        registry = odoo.modules.registry.Registry(user_database.name)
        with registry.cursor() as cr:
            context = {}
            env = api.Environment(cr, SUPERUSER_ID, context)
	    env['ir.config_parameter'].set_param(cr, SUPERUSER_ID, 'subscription_status', 'canceled' )

        return werkzeug.utils.redirect("/saas/portal")        

    @http.route('/saas/subscribe', type="http", auth="user")
    def saas_subscribe_process(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value

        database_name = values['database']
        user_database = request.env['saas.database'].search([('name','=',database_name), ('partner_id','=', request.env.user.partner_id.id)])
        payment_method = request.env['payment.token'].search([('id','=', int(values['payment_method']) ), ('partner_id','=',request.env.user.partner_id.id)]  )        

        user_database.sudo().state = "subscribed"
        user_database.sudo().next_payment_date = datetime.now()  + relativedelta(months=1)
        user_database.sudo().payment_method_id = payment_method.id
        user_database.sudo().subscription_cost = user_database.template_database_id.price

        #Connect to the saas database and update the subscription status
	db = openerp.sql_db.db_connect(user_database.name)

        registry = odoo.modules.registry.Registry(user_database.name)
        with registry.cursor() as cr:
            context = {}
            env = api.Environment(cr, SUPERUSER_ID, context)
	    env['ir.config_parameter'].set_param('subscription_status', 'subscribed' )

        return werkzeug.utils.redirect("/saas/portal")        


    @http.route('/saas/add/payment/process', type="http", auth="public", website=True)
    def saas_add_payment_process(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
	    values[field_name] = field_value

        card_number = values['card_number']
        card_type = values['type']
        owner = values['owner']
        owner_first = owner.split(" ")[0]
        owner_last = owner.split(" ")[1]
        expiration_date_month = values['expiration_date_month']
        expiration_date_year = values['expiration_date_year']
        cvv = values['cvv']

        payment_aquirer = request.env['ir.model.data'].get_object('payment', 'payment_acquirer_paypal')

        #Request access
        base_url = ""
        if payment_aquirer.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        else:
            base_url = "https://api.paypal.com/v1/oauth2/token"

	payload = {'grant_type':"client_credentials"}
	client_id = payment_aquirer.paypal_client_id
	secret = payment_aquirer.paypal_secret
	response_string = requests.post(base_url, data=payload, auth=(str(client_id), str(secret)), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept-Language": "en_US"})
                    
        json_ob = json.loads(response_string.text)            
        
        if 'access_token' in json_ob:
            payment_aquirer.sudo().paypal_api_access_token = json_ob['access_token']
        else:
            return response_string.text
            
        base_url = ""
        if payment_aquirer.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/vault/credit-cards/"
        else:
            base_url = "https://api.paypal.com/v1/vault/credit-cards/"
        
        access_token = payment_aquirer.paypal_api_access_token
        card_partner = request.env.user.partner_id
        payload = {
            'number': card_number.replace(" ",""),
            'type': card_type,
            'expire_month': expiration_date_month,
            'expire_year': expiration_date_year,
            'cvv2': cvv,
            #'first_name': owner_first,
            #'last_name': owner_last,
            #'billing_address':  { "line1": card_partner.street, "city": card_partner.city, 'country_code': card_partner.country_id.code, 'postal_code': card_partner.zip, 'state':card_partner.state_id.code, 'phone':card_partner.phone},
            'external_customer_id': "res_partner_" + str(request.env.user.partner_id.id)
        }
        
        response_string = requests.post(base_url, data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token})

        json_ob = json.loads(response_string.text)
        
        if 'id' in json_ob:
            credit_card_token = json_ob['id']
            hidden_name = "**** **** **** *" + card_number[-3:]
            request.env['payment.token'].sudo().create({'name': hidden_name,'partner_id': request.env.user.partner_id.id, 'active': True, 'acquirer_id': payment_aquirer.id, 'acquirer_ref': credit_card_token})    
            
            return werkzeug.utils.redirect("/saas/portal")

        else:
            error_string = ""
            
            for paypal_error in json_ob['details']:
                error_string += paypal_error['issue'] + "\n"
            
            return error_string


    @http.route('/saas/package/details/<template_id>', type="http", auth="public", website=True)
    def saas_package_details(self, template_id, **kw):
        template_database = request.env['saas.template.database'].browse( int(template_id) )
        
        return http.request.render('sythil_saas_server.saas_package_details', {'template_database': template_database})    
    
    @http.route('/template/details/<template_id>', type="http", auth="public", website=True)
    def template_details(self, template_id, **kw):
        """Lists what is inside the template database"""

        template_database = request.env['saas.template.database'].browse( int(template_id) )
        
        #connect to the newly created database
	db = openerp.sql_db.db_connect(template_database.database_name)

        page_data_applications = ""
        page_data_builtin = ""
        page_data_community = ""
        groups_string = ""
        
        buildin_modules_list = []
        for buildin_module in request.env['saas.modules.builtin'].search([]):
            buildin_modules_list.append(buildin_module.name)

        registry = odoo.modules.registry.Registry(template_database.database_name)
        with registry.cursor() as cr:
            context = {}
            env = api.Environment(cr, SUPERUSER_ID, context)
	    
	    #Application list
	    application_modules = env['ir.module.module'].search([('state','=','installed'), ('application','=',True) ])
	    for installed_module_id in application_modules:
	        installed_module = env['ir.module.module'].browse(installed_module_id)
	        page_data_applications += "<h3>" + installed_module.shortdesc + " (" + installed_module.name + ")</h3>"
	        
	    #Built in modules
	    builtin_modules = env['ir.module.module'].search([('state','=','installed'), ('application','=',False)])
	    for installed_module_id in builtin_modules:
	        installed_module = env['ir.module.module'].browse(installed_module_id)
	        if installed_module.name in buildin_modules_list:
	            page_data_builtin += "<h3>" + installed_module.shortdesc + " (" + installed_module.name + ")</h3>"
	    
	    #Community Modules
	    community_modules = env['ir.module.module'].search([('state','=','installed')])
	    for installed_module_id in community_modules:
	        installed_module = env['ir.module.module'].browse(installed_module_id)
	        if installed_module.name not in buildin_modules_list:
	            page_data_community += "<h3><a href=\"https://www.odoo.com/apps/modules/10.0/" + installed_module.name + "\">" + installed_module.shortdesc + " (" + installed_module.name + ")</a></h3>"
	            
	    saas_user_id = env['ir.model.data'].get_object_reference('sythil_saas_client', 'saas_user')[1]
            saas_user = env['res.users'].browse(saas_user_id)
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

        installed_module_string = ""
        my_return = []

	#Get a list of installed modules on the template database
        registry = odoo.modules.registry.Registry(template_database.database_name)

	#Update the saas user's name, email, login and password
        with registry.cursor() as cr:
            context = {}
            env = api.Environment(cr, SUPERUSER_ID, context)

	    for installed_module_id in env['ir.module.module'].search([('state','=','installed')] ):
	        installed_module = env['ir.module.module'].browse(installed_module_id )	        
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
        system_name = system_name.lower()
        
        if system_name.isalnum() == False:
            return "Only AlphaNumeric characters allowed"

        #Check if this email has been used to create a SAAS system before
        if request.env['saas.database'].sudo().search_count([('login','=',email)]) > 0:
            return "This email has already been used to create a SAAS system"

	#Get the template database
	template_database = request.env['saas.template.database'].browse(int(values["package"]))
	chosen_template = template_database.database_name

	#Create the new user
	new_user = request.env['res.users'].sudo().create({'name': person_name, 'login': values['email'], 'email': values['email'], 'password': values['password'] })
	
	#Add the user to the saas portal group
	saas_portal_group = request.env['ir.model.data'].sudo().get_object('sythil_saas_server', 'saas_portal_group')
        saas_portal_group.users = [(4, new_user.id)]

        #Remove 'Contact Creation' permission        
	contact_creation_group = request.env['ir.model.data'].sudo().get_object('base', 'group_partner_manager')
        contact_creation_group.users = [(3,new_user.id)]

        #Also remove them as an employee
	human_resources_group = request.env['ir.model.data'].sudo().get_object('base', 'group_user')
        human_resources_group.users = [(3,new_user.id)]

        #Create the associated company(res.partner) record
        saas_tag = request.env['ir.model.data'].sudo().get_object('sythil_saas_server', 'saas_client_tag')
        new_user.partner_id.write({'name': company, 'company_type':'company', 'email': email, 'category_id': [(4,saas_tag.id)] })
        new_company = new_user.partner_id
        new_company.child_ids.sudo().create({'parent_id': new_company.id, 'type':'contact', 'name':person_name, 'email': email, 'category_id': [(4,saas_tag.id)] })
        
	#Add this database to the saas list
	trial_expiration_date = datetime.now()  + timedelta(days=template_database.trial_duration)
	new_saas_database = request.env['saas.database'].sudo().create({'name':system_name, 'login': email, 'password': password, 'template_database_id': template_database.id, 'partner_id': new_company.id, 'user_id':new_user.id, 'state': 'trial', 'trial_expiration': trial_expiration_date}) 
        
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

        registry = odoo.modules.registry.Registry(db_name)

	#Update the saas user's name, email, login and password
        with registry.cursor() as cr:
            context = {}
            env = api.Environment(cr, SUPERUSER_ID, context)
	    saas_user = env['ir.model.data'].get_object('sythil_saas_client', 'saas_user')
	    saas_user.write({'name':person_name, 'email':email, 'login':email, 'password':password})
	    saas_company = env['ir.model.data'].get_object('base', 'main_company')
	    saas_company.name = company
	    
	    #Init the trial period
	    env['ir.config_parameter'].set_param('subscription_status', 'trial' )
	    env['ir.config_parameter'].set_param('trial_expiration_date', trial_expiration_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT) )
	    env['ir.config_parameter'].set_param('saas_server_url', request.httprequest.host_url)
	    
	    #Randomise the super admin password to maxamise security
	    random_password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))
	    saas_super_user = env['ir.model.data'].get_object('base', 'user_root')
	    saas_super_user.write({'password':random_password})
	    
	    #Store it for later use with the login button
	    new_saas_database.super_admin_login = saas_super_user.login
	    new_saas_database.super_admin_password = random_password
        
        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])
        
        return werkzeug.utils.redirect("/saas/portal")        
        
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