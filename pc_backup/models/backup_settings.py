# -*- coding: utf-8 -*-
import socket
import threading
import random
import string
import logging
import requests
_logger = logging.getLogger(__name__)
from openerp.http import request
import odoo
from openerp import api, fields, models

class BackupSettings(models.Model):

    _name = "backup.settings"
    _inherit = 'res.config.settings'
            
    backup_mode = fields.Selection([('full','Full Backup')], string="Backup Mode")
    odoo_backup_days = fields.Integer(string="Days to keep backups")
    
    #-----Backup Mode-----

    @api.multi
    def get_default_backup_mode(self, fields):
        return {'backup_mode': self.env['ir.values'].get_default('backup.settings', 'backup_mode')}

    @api.multi
    def set_default_backup_mode(self):
        for record in self:
            self.env['ir.values'].set_default('backup.settings', 'backup_mode', record.backup_mode)
            
    #-----Odoo Backup Days-----

    @api.multi
    def get_default_odoo_backup_days(self, fields):
        return {'odoo_backup_days': self.env['ir.values'].get_default('backup.settings', 'odoo_backup_days')}

    @api.multi
    def set_default_odoo_backup_days(self):
        for record in self:
            self.env['ir.values'].set_default('backup.settings', 'odoo_backup_days', record.odoo_backup_days)