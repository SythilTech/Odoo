# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
import odoo

from openerp import api, fields, models

class WebsiteSupportSettingsInherit(models.TransientModel):

    _inherit = 'website.support.settings'
    
    timesheet_default_project_id = fields.Many2one('project.project', string="Default Timesheet Project")

    @api.multi
    def set_values(self):
        super(WebsiteSupportSettingsInherit, self).set_values()
        self.env['ir.default'].set('website.support.settings', 'timesheet_default_project_id', self.timesheet_default_project_id.id)

    @api.model
    def get_values(self):
        res = super(WebsiteSupportSettingsInherit, self).get_values()
        res.update(
            timesheet_default_project_id=self.env['ir.default'].get('website.support.settings', 'timesheet_default_project_id'),
        )
        return res