from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_settings(models.Model):

    _name = "esms.settings"
    _inherit = 'res.config.settings'
    
    auto_e164 = fields.Boolean(string='Auto Convert Numbers to E.164', default=True, help="This feature can sometimes go a bit rogue so disabling can help solve issues")
    
    @api.model
    def get_default_auto_e164(self, fields):
        settings = self.env['esms.settings'].browse(0)
        return {'auto_e164': settings.auto_e164}

    @api.model
    def set_auto_e164(self, ids):
        settings = self.browse(0)
        settings.write({'auto_e164': settings.auto_e164})
