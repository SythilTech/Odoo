# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class SaasSettings(models.Model):

    _name = "saas.settings"
    _inherit = 'res.config.settings'
    
    @api.model
    def get_default_system_redirect(self, fields):
        return {'system_redirect': self.env['ir.values'].get_default('saas.settings', 'system_redirect')}
        
    @api.multi
    def set_system_redirect(self):
        for record in self:
            self.env['ir.values'].set_default('saas.settings', 'system_redirect', record.system_redirect)
    
    system_redirect = fields.Selection([('db_filter','DB Filter'), ('subdomain','Sub Domain')], string="System Redirect", help="URL the user gets redirected to after creating the new system\nDB Filter = http://mydomain.com.au/web?db=db_name\nsubdomain = systemname.mydoain.com.au")