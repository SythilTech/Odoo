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
    user_id = fields.Many2one('res.users', string="SAAS User")
    access_url = fields.Char(string="Access URL", compute="_compute_access_url")
    
    @api.depends('name')
    def _compute_access_url(self):
        system_redirect = self.env['ir.config_parameter'].get_param('saas_system_redirect')
        
        if system_redirect == "db_filter":
            self.access_url = "http://" + request.httprequest.host + "/web?db=" + self.name
        elif system_redirect == "subdomain":
            self.access_url = "http://" + self.name + "." + request.httprequest.host

