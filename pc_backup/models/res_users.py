# -*- coding: utf-8 -*-
from openerp import api, fields, models

class BackupUser(models.Model):

    _inherit = "res.users"
    
    backup_user = fields.Boolean(string="Backup User")