# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasMultiDB(http.Controller):

    @http.route('/tryodoo', type="http", auth="public", website=True)
    def saas_submit(self, **kw):
        """Webpage that let's a uer create a new db"""
        return http.request.render('saas_multi_db.saas_submit', {})

    @http.route('/saas/createdb', type="http", auth="public")
    def saas_create_datadb(self, **kwargs):
        """Creates the new database"""
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	
	email = values["email"] 
	name = values["system_name"]
	person_name = values["name"]
	demo = False
	lang = "en_AU"
		    
	db = openerp.sql_db.db_connect('postgres')
	with closing(db.cursor()) as cr:
	    #get the templaste database
	    chosen_template = openerp.tools.config['db_template']
	        
	    #Check if the database already exists
	    cr.execute("SELECT datname FROM pg_database WHERE datname = %s",(name,))
	    if cr.fetchall():
	        return "Database Already Exists"
	        
	    #create the new database
	    cr.autocommit(True)     # avoid transaction block
	    cr.execute("""CREATE DATABASE "%s" ENCODING 'unicode' TEMPLATE "%s" """ % (name, chosen_template))

            #connect to the newly created database
	    db = openerp.sql_db.db_connect(name)

            #Create new registry
            registry = openerp.modules.registry.RegistryManager.new(name, demo, None, update_module=True)

	    #Add this database to the saas list
	    request.env['saas.database'].create({'name':name})
            
            #Create SAAS partner for campaigns etc
            request.env['res.partner'].sudo().create({'name':person_name, 'email':email, 'saas_partner':'True'})
            
	    with closing(db.cursor()) as cr:
	        
	        #Update the translations of each installed module
	        if lang:
	            modobj = registry['ir.module.module']
	            mids = modobj.search(cr, SUPERUSER_ID, [('state', '=', 'installed')])
	            modobj.update_translations(cr, SUPERUSER_ID, mids, lang)

	        #Update admin's password
	        #registry['res.users'].write(cr, SUPERUSER_ID, [SUPERUSER_ID], {'password': 'sythil'})

	        #Add SAAS user
	        #saas_user_id = registry['res.users'].create(cr, SUPERUSER_ID, {'name': person_name, 'email': email, 'login': email, 'password': password, 'lang': lang})
                #saas_user = registry['res.users'].browse(cr, SUPERUSER_ID, saas_user_id)
                
                #Install Project module
                #crm_module_id = registry['ir.module.module'].search(cr, SUPERUSER_ID, [('name','=','project')])[0]
                #crm_module = registry['ir.module.module'].browse(cr, SUPERUSER_ID, crm_module_id)
                #crm_module.button_immediate_install()

                
                #Add user to the project manager group
                #full_xid = "project.group_project_manager"
                #group_module = full_xid.split(".")[0]
                #group_xid = full_xid.split(".")[1]
                #user_group = registry['ir.model.data'].get_object(cr, SUPERUSER_ID, group_module, group_xid)
                #saas_user.groups_id  = [(4, user_group.id)]
                
                #Log the user in
		request.session.authenticate(name, 'admin', '')
                	
		return http.local_redirect('/web/')
