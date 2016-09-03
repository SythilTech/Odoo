# -*- coding: utf-8 -*-
from openerp import api, fields, models

class BackupBackup(models.Model):

    _name = "backup.backup"
    
    user_id = fields.Many2one('res.users', string="User")
    backup_file = fields.Binary(string="Backup File")