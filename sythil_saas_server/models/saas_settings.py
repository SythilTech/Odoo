# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

class SaasSettings(models.TransientModel):

    _inherit = "res.config.settings"
    _name = "saas.settings"
    
    @api.model
    def get_default_system_redirect(self, fields):
        return {'system_redirect': self.env['ir.config_parameter'].get_param('saas_system_redirect') }
        
    @api.one
    def set_system_redirect(self):
        self.env['ir.config_parameter'].set_param('saas_system_redirect', self.system_redirect)
    
    system_redirect = fields.Selection([('db_filter','DB Filter'), ('subdomain','Sub Domain')], string="System Redirect", help="URL the user gets redirected to after creating the new system\nDB Filter = http://mydomain.com.au/web?db=db_name\nsubdomain = systemname.mydoain.com.au")