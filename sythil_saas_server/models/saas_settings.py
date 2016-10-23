# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
import openerp
import optparse
import openerp.release as release

from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

from openerp.tools.config import configmanager
from openerp.tools.config import MyOption

class SaasSettings(models.TransientModel, configmanager):

    _inherit = "res.config.settings"
    _name = "saas.settings"
    
    @api.model
    def get_default_system_redirect(self, fields):
        return {'system_redirect': self.env['ir.config_parameter'].get_param('saas_system_redirect') }
        
    @api.one
    def set_system_redirect(self):
        self.env['ir.config_parameter'].set_param('saas_system_redirect', self.system_redirect)
    
    system_redirect = fields.Selection([('db_filter','DB Filter'), ('subdomain','Sub Domain')], string="System Redirect", help="URL the user gets redirected to after creating the new system\nDB Filter = http://mydomain.com.au/web?db=db_name\nsubdomain = systemname.mydoain.com.au")
    
    @api.one
    def add_saas_setting(self):
        
        version = "%s %s" % (release.description, release.version)
        self.parser = parser = optparse.OptionParser(version=version, option_class=MyOption)

        group = optparse.OptionGroup(parser, "Web interface Configuration")
        group.add_option("--sythil-saas-database", dest="sythilsaasserver", my_default='" + self.env.cr.dbname + "',help="SAAS Database", metavar="REGEXP")
        parser.add_option_group(group)
                
    @api.one
    def saas_server_setting(self):
        _logger.error(openerp.conf.server_wide_modules)
        _logger.error(openerp.tools.config['sythilsaasserver'])