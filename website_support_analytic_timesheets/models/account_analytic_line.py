# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicketInheritAccountAnalyticLine(models.Model):

    _inherit = "account.analytic.line"

    support_ticket_id = fields.Many2one('website.support.ticket', string="Support Ticket")