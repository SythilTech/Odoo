# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritAccountAnalyticLine(models.Model):

    _inherit = "account.analytic.line"

    support_ticket_id = fields.Many2one('website.support.ticket', string="Support Ticket")
    person_name = fields.Char(related="support_ticket_id.person_name", string="Customer Name")
    ticket_number_display = fields.Char(related="support_ticket_id.ticket_number_display", string="Ticket Number")
    state = fields.Many2one('website.support.ticket.states', readonly=True, related="support_ticket_id.state", string="State")
    open_time = fields.Datetime(related="support_ticket_id.create_date", string="Open Time")    
    close_time = fields.Datetime(related="support_ticket_id.close_time", string="Close Time")
    planned_hours = fields.Float(string='Initially Planned Hours', related="task_id.planned_hours", help='Estimated time to do the task, usually set by the project manager when the task is in draft state.')    
    remaining_hours = fields.Float(string='Remaining Hours', related="task_id.remaining_hours", digits=(16,2), help="Total remaining time, can be re-estimated periodically by the assignee of the task.")    
    total_hours = fields.Float(string='Total', related="task_id.total_hours", help="Computed as: Time Spent + Remaining Time.")
    effective_hours = fields.Float(string='Hours Spent', related="task_id.effective_hours", help="Computed using the sum of the task work done.")