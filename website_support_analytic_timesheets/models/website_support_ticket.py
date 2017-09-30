# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritTimesheets(models.Model):

    _inherit = "website.support.ticket"
    
    analytic_timesheet_ids = fields.One2many('account.analytic.line', 'support_ticket_id', string="Timesheet")