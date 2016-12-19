# -*- coding: utf-8 -*-

import datetime

from openerp import api, fields, models

class BackupOdoo(models.Model):

    _name = "backup.odoo"
    _description = "Odoo Database Backup"
    
    user_id = fields.Many2one('res.users', string="User")
    backup_type = fields.Selection([('full','Full Backup')], string="Backup Type", default="full")
    database_name = fields.Char(string="Database Name")
    data = fields.Binary(string="Data")
    data_filename = fields.Char("Data Filename")
    
    @api.model
    def backup_cleanup(self):
        
        backup_days_to_keep = 7
        
        for backup in self.env['backup.odoo'].sudo().search([]):
            if backup.create_date < (datetime.datetime.now() - datetime.timedelta(days=backup_days_to_keep) ).strftime("%Y-%m-%d %H:%M:%S"):
                backup.unlink()