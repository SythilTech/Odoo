# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from contextlib import closing
import os
import shutil
import datetime
import json
import tempfile
import base64

import openerp
from openerp import api, fields, models

class SaasTemplateDatabase(models.Model):

    _name = "saas.template.database"
    _description = "Preconfigured databases that the website user can select from"""
    
    name = fields.Char(string="Display Name", help="Displayed on the website")
    database_name = fields.Char(string="Database Name", help="The name of the template database in psql")
    trial_duration = fields.Integer(string="Trial Duration (days)")
    image = fields.Binary(string="Image")
    product_id = fields.Many2one('product.template', string="Saas Product", help="Place to put price and other details")
    price = fields.Float(string="Price")
    description = fields.Char(string="Description", default="Placeholder description")
    html_description = fields.Html(string="HTML Description")
    saas_database_ids = fields.One2many('saas.database', 'template_database_id', string="SAAS Databases")
    auto_backup = fields.Boolean(string="Auto Backup")
    auto_backup_days_to_keep = fields.Integer(string="Auto Backup Days to Keep", default="7")
    
    @api.model
    def saas_auto_backup(self):
        
        for template_database in self.env['saas.template.database'].search([('auto_backup','=',True)]):
            for saas_database in template_database.saas_database_ids:
                for backup in saas_database.backup_ids:
                    if backup.create_date < (datetime.datetime.now() - datetime.timedelta(days=template_database.auto_backup_days_to_keep) ).strftime("%Y-%m-%d %H:%M:%S"):
                        backup.unlink()
                
                with openerp.tools.osutil.tempdir() as dump_dir:
                    db_name = saas_database.name
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
            
                    t.seek(0)
                    save_name = db_name + ' ' +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Backup'
                    file_name = db_name + ' ' +  datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '.zip'
                    self.env['ir.attachment'].create({'name': save_name, 'mimetype': 'application/zip', 'datas_fname': file_name, 'type': 'binary', 'datas': base64.b64encode( t.read() ) , 'description': 'Automatic backup of ' + db_name + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'res_model': 'saas.database', 'res_id':  saas_database.id, 'res_name': save_name, 'saas_database_id': saas_database.id})

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