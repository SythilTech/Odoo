# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

class SaasDatabase(models.Model):

    _name = "saas.database"
    
    partner_id = fields.Many2one('res.partner', string="Partner", help="Company that owns the data")
    name = fields.Char(string="Database Name")
    login = fields.Char(string="Login")
    password = fields.Char(string="Password")
    template_database_id = fields.Many2one('saas.template.database', string="Template Database", ondelete="SET NULL")
    backup_ids = fields.One2many('ir.attachment', 'saas_database_id', string="Backups")