# -*- coding: utf-8 -*-
from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError

class WebsiteSupportTicketInheritTimesheets(models.Model):

    _inherit = "website.support.ticket"
        
    analytic_timesheet_ids = fields.One2many('account.analytic.line', 'support_ticket_id', string="Timesheet")
    timesheet_project_id = fields.Many2one('project.project', string="Timesheet Project", compute="_compute_timesheet_project_id")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", compute="_compute_analytic_account_id")

    @api.multi
    def open_close_ticket_wizard(self):

        timesheet_count = len(self.analytic_timesheet_ids)
        
        if timesheet_count == 0:
            raise UserError("Timesheets must be filled in before the ticket can be closed")

        return {
            'name': "Close Support Ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.support.ticket.close',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }

    @api.multi
    def _compute_analytic_account_id(self):

        default_analytic_account = self.env['ir.model.data'].get_object('website_support_analytic_timesheets', 'customer_support_account')

        for record in self:
            record.analytic_account_id = default_analytic_account.id

    @api.multi
    def _compute_timesheet_project_id(self):
        
        setting_timesheet_default_project_id = self.env['ir.default'].get('website.support.settings', 'timesheet_default_project_id')
        
        for record in self:
        
            if setting_timesheet_default_project_id:
                record.timesheet_project_id = setting_timesheet_default_project_id
