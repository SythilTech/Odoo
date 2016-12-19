# -*- coding: utf-8 -*-
import xmlrpclib
import tempfile
import base64
import openerp
import os
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import shutil
import json
import datetime
import odoo

from openerp import api, fields, models

class BackupServer(models.Model):

    _name = "backup.server"
    _description = "Odoo Backup Server"
    
    name = fields.Char(string="Name")
    host = fields.Char(string="Host URL")
    database_name = fields.Char(string="Database Name")
    username = fields.Char(string="Username")
    password = fields.Char(string="Password")

    def test_backup_server(self):
    
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(self.host))
        uid = common.authenticate(self.database_name, self.username, self.password, {})
            
        if uid:
            raise UserError("Test successful")        
        else:
            raise UserError("Test failed")        
            
    @api.model
    def backup_now(self):
        _logger.error("backup now")

        db_name = self.env.cr.dbname
        cmd = ['pg_dump', '--no-owner']
        cmd.append(db_name)

        t=tempfile.TemporaryFile()

        with odoo.tools.osutil.tempdir() as dump_dir:
            filestore = odoo.tools.config.filestore(db_name)
            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(self.dump_db_manifest(cr), fh, indent=4)
            cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
            odoo.tools.exec_pg_command(*cmd)

            
            odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
            t.seek(0)
            save_name = db_name + ' ' +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Backup'
            file_name = db_name + ' ' +  datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '.zip'


        for backup_server in self.env['backup.server'].sudo().search([]):
                #Connect to the backup server and save the database
                common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(backup_server.host))
                uid = common.authenticate(backup_server.database_name, backup_server.username, backup_server.password, {})
                models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(backup_server.host))
                backup = models.execute_kw(backup_server.database_name, uid, backup_server.password,'backup.odoo', 'create',[{'user_id':uid, 'backup_type': 'full', 'database_name': self.env.cr.dbname, 'data': base64.b64encode( t.read() ), 'data_filename': file_name}])

    @api.model
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
        
class BackupServerBackup(models.Model):

    _name = "backup.server.backup"
    _description = "Odoo Backup Server Backup"

    backup_server_id = fields.Many2one('backup.server', string="Backup Server")    
    name = fields.Char(string="Name")