# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerTicket(models.Model):

    _inherit = "res.partner"

    support_ticket_ids = fields.One2many('website.support.ticket', 'partner_id', string="Tickets")
    support_ticket_count = fields.Integer(compute="_count_support_tickets", string="Ticket Count")
    new_support_ticket_count = fields.Integer(compute="_count_new_support_tickets", string="New Ticket Count")
    support_ticket_string = fields.Char(compute="_compute_support_ticket_string", string="Support Ticket String")
    stp_ids = fields.Many2many('res.partner', 'stp_res_partner_rel', 'stp_p1_id', 'stp_p2_id', string="Support Ticket Access Accounts", help="(DEPRICATED use departments) Can view support tickets from other contacts")
    sla_id = fields.Many2one('website.support.sla', string="SLA")
    dedicated_support_user_id = fields.Many2one('res.users', string="Dedicated Support User")
    ticket_default_email_cc = fields.Char(string="Default Email CC")
    ticket_default_email_body = fields.Text(string="Default Email Body")

    @api.multi
    def create_support_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'website.support.ticket',
            'view_mode': 'form',
            'context': {'default_partner_id': self.id},
            'target': 'new',
        }

    @api.one
    @api.depends('support_ticket_ids')
    def _count_support_tickets(self):
        """Sets the amount support tickets owned by this customer"""
        self.support_ticket_count = self.support_ticket_ids.search_count([('partner_id','=',self.id)])

    @api.one
    @api.depends('support_ticket_ids')
    def _count_new_support_tickets(self):
        """Sets the amount of new support tickets owned by this customer"""
        opened_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_open')
        self.new_support_ticket_count = self.support_ticket_ids.search_count([('partner_id','=',self.id), ('state','=',opened_state.id)])

    @api.one
    @api.depends('support_ticket_count', 'new_support_ticket_count')
    def _compute_support_ticket_string(self):
        self.support_ticket_string = str(self.support_ticket_count) + " (" + str(self.new_support_ticket_count) + ")"