# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritAccountAnalyticLine(models.Model):

    _inherit = "account.analytic.line"

    support_ticket_id = fields.Many2one('website.support.ticket', string="Support Ticket")
    ticket_number_display = fields.Char(related="support_ticket_id.ticket_number_display", string="Ticket Number")
    state = fields.Many2one('website.support.ticket.states', readonly=True, related="support_ticket_id.state", string="State")
    open_time = fields.Datetime(related="support_ticket_id.create_date", string="Open Time")    
    close_time = fields.Datetime(related="support_ticket_id.close_time", string="Close Time")