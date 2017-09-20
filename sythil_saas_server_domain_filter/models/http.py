# -*- coding: utf-8 -*-
import odoo
import openerp
from odoo import api
import re
import logging
_logger = logging.getLogger(__name__)
from openerp.http import request

original_db_filter = odoo.http.db_filter

def db_filter(dbs, httprequest=None):

    httprequest = httprequest or request.httprequest
    h = httprequest.environ.get('HTTP_HOST', '').split(':')[0]
    d, _, r = h.partition('.')
    if d == "www" and r:
        d = r.partition('.')[0]
    r = odoo.tools.config['dbfilter'].replace('%h', h).replace('%d', d)
    dbs = [i for i in dbs if re.match(r, i)]

    saas_server_db = odoo.tools.config['sythilsaasserver']
    
    #connect to the saas server database
    db = openerp.sql_db.db_connect(saas_server_db)

    #Create new registry
    registry = odoo.modules.registry.Registry(saas_server_db)

    #Get the database which matches the domain
    with registry.cursor() as cr:
        context = {}
        env = api.Environment(cr, odoo.SUPERUSER_ID, context)

        saas_domain = env['saas.database.domain'].search([('name','=',h)])

        if saas_domain:
	    #Select only that database
	    dbs = [saas_domain.database_id.name]

    return dbs
        
odoo.http.db_filter = db_filter