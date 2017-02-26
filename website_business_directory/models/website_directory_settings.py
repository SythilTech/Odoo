# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class WebsiteDirectorySettings(models.TransientModel):

    _name = "website.directory.settings"
    _inherit = 'res.config.settings'
    
    privacy_mode = fields.Selection([('public','Public'), ('private','Private')], help="Private requires users to login before they can see any listings", string="Privacy Setting")
    
    @api.multi
    def get_default_privacy_mode(self):
        return {'privacy_mode': self.env['ir.values'].get_default('website.directory.settings', 'privacy_mode')}

    @api.multi
    def set_default_privacy_mode(self):
        for record in self:
            self.env['ir.values'].set_default('website.directory.settings', 'privacy_mode', record.privacy_mode)