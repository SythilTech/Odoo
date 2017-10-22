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

    #-----Timesheet Default Project-----

    @api.multi
    def get_default_timesheet_default_project_id(self, fields):
        return {'timesheet_default_project_id': self.env['ir.values'].get_default('website.support.settings', 'timesheet_default_project_id')}

    @api.multi
    def set_default_timesheet_default_project_id(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'timesheet_default_project_id', record.timesheet_default_project_id.id)