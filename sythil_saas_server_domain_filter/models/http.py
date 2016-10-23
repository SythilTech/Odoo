# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from contextlib import closing
from openerp import api, fields, models
import openerp.http as http
from openerp.http import request
from openerp.tools.config import configmanager
import openerp
from openerp import SUPERUSER_ID
import re

def db_filter(dbs, httprequest=None):

    httprequest = httprequest or request.httprequest
    h = httprequest.environ.get('HTTP_HOST', '').split(':')[0]
    d, _, r = h.partition('.')
    if d == "www" and r:
        d = r.partition('.')[0]
    r = openerp.tools.config['dbfilter'].replace('%h', h).replace('%d', d)

    saas_server_db = openerp.tools.config['sythilsaasserver']

    #connect to the saas server database
    db = openerp.sql_db.db_connect(saas_server_db)

    #Create new registry
    registry = openerp.modules.registry.RegistryManager.new(saas_server_db, False, None, update_module=True)

    dbs = [i for i in dbs if re.match(r, i)]

    #Get the database which matches the domain
    with closing(db.cursor()) as cr:
        cr.autocommit(True)     # avoid transaction block
	saas_domain_id = registry['saas.database.domain'].search(cr, SUPERUSER_ID, [('name','=',h)])

        if saas_domain_id:
	    saas_domain = registry['saas.database.domain'].browse(cr, SUPERUSER_ID, saas_domain_id[0])
	    
	    #Select only that database
	    dbs = [saas_domain.database_id.name]

    return dbs

http.db_filter = db_filter
