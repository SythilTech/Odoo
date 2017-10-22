# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritTimesheets(models.Model):

    _inherit = "website.support.ticket"
        
    analytic_timesheet_ids = fields.One2many('account.analytic.line', 'support_ticket_id', string="Timesheet")
    timesheet_project_id = fields.Many2one('project.project', string="Timesheet Project", compute="_compute_timesheet_project_id")
    
    @api.multi
    def _compute_timesheet_project_id(self):
        
        setting_timesheet_default_project_id = self.env['ir.values'].get_default('website.support.settings', 'timesheet_default_project_id')
        
        for record in self:
        
            if setting_timesheet_default_project_id:
                record.timesheet_project_id = setting_timesheet_default_project_id
