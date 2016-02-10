# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from contextlib import closing
import os
import shutil

import openerp
from openerp import api, fields, models

class SaasTemplateDatabase(models.Model):

    _name = "saas.template.database"
    _description = "Preconfigured databases that the website user can select from"""
    
    name = fields.Char(string="Display Name", help="Displayed on the website")
    database_name = fields.Char(string="Database Name", help="The name of the template database in psql")
    image = fields.Binary(string="Image")
    description = fields.Char(string="Description")
    monthly_price = fields.Float(string="Monthly Price")
    create_instance = fields.Boolean(string="Create New Instance")
      
    @api.one
    def save_template(self):
        db_original_name = self.database_name
        db_name = db_original_name + "_clone"
        
        openerp.sql_db.close_db(db_original_name)
        db = openerp.sql_db.db_connect('postgres')
        
        with closing(db.cursor()) as cr:
            cr.autocommit(True)     # avoid transaction block
            self._drop_conn(cr, db_original_name)
            
            #Check if the database already exists
	    cr.execute("SELECT datname FROM pg_database WHERE datname = %s",(db_name,))
	    if cr.fetchall():
	        cr.execute("""DROP DATABASE "%s" """ % (db_name,))
	        
            cr.execute("""CREATE DATABASE "%s" ENCODING 'unicode' TEMPLATE "%s" """ % (db_name, db_original_name))

        from_fs = openerp.tools.config.filestore(db_original_name)
        to_fs = openerp.tools.config.filestore(db_name)
        
        if os.path.exists(from_fs) and not os.path.exists(to_fs):
            shutil.copytree(from_fs, to_fs)

    @api.one
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