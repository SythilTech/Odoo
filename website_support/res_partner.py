from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class ResPartnerTicket(models.Model):

    _inherit = "res.partner"
    
    support_ticket_ids = fields.One2many('website.support.ticket', 'partner_id', string='Tickets')
    support_ticket_count = fields.Integer(compute="_count_support_tickets", string="Ticket Count")
    
    @api.one
    @api.depends('support_ticket_ids')
    def _count_support_tickets(self):
        self.support_ticket_count = self.support_ticket_ids.search_count([('partner_id','=',self.id)])