# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerTicket(models.Model):

    _inherit = "res.partner"
    
    support_ticket_ids = fields.One2many('website.support.ticket', 'partner_id', string='Tickets')
    support_ticket_count = fields.Integer(compute="_count_support_tickets", string="Ticket Count")
    
    @api.one
    @api.depends('support_ticket_ids')
    def _count_support_tickets(self):
        """Sets the amount support tickets owned by this customer"""
        self.support_ticket_count = self.support_ticket_ids.search_count([('partner_id','=',self.id)])