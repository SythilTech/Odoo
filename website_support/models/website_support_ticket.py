# -*- coding: utf-8 -*-
from openerp import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class WebsiteSupportTicket(models.Model):

    _name = "website.support.ticket"
    _description = "Website Support Ticket"
    _rec_name = "subject"
    _inherit = ['mail.thread','ir.needaction_mixin']

    def _default_state(self):
        open_state = self.env['website.support.ticket.states'].search([('name','=','Open')])
        return open_state[0]
    
    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    person_name = fields.Char(required=True, string='Person Name', readonly=True)
    email = fields.Char(string="Email", readonly=True)
    category = fields.Many2one('website.support.ticket.categories', string="Category", required=True, track_visibility='onchange')
    subject = fields.Char(string="Subject", readonly=True)
    description = fields.Text(string="Description", readonly=True)
    state = fields.Many2one('website.support.ticket.states', required=True, readonly=True, default=_default_state, string="State")
    conversation_history = fields.One2many('website.support.ticket.message', 'ticket_id', string="Conversation History (Depreciated)")
    attachment = fields.Binary(string="Attachments")
    attachment_filename = fields.Char(string="Attachment Filename")

    @api.model
    def _needaction_domain_get(self):
        return ['|',('state', '=', 'Open'), ('state', '=', 'Customer Replied')]

    @api.multi
    def write(self, values, context=None):

        update_rec = super(WebsiteSupportTicket, self).write(values)

        #Email user if category has changed
        if 'category' in values:
            change_category_email = self.env['ir.model.data'].sudo().get_object('website_support', 'new_support_ticket_category_change')
            change_category_email.send_mail(self.id, True)
        
        return update_rec

    @api.one
    def close_ticket(self):

        new_state = self.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_staff_closed')
        
        #We record state change manually since it would spam the chatter if every 'Staff Replied' and 'Customer Replied' gets recorded
        message = "<ul class=\"o_mail_thread_message_tracking\">\n<li>State:<span> " + self.state.name + " </span><b>-></b> " + new_state.name + " </span></li></ul>"
        self.message_post(body=message, subject="Ticket Closed by Staff")

        self.state = new_state.id

        #Send an email notifing the customer  that the ticket has been closed
        ticket_closed_email = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_closed')
        ticket_closed_email.send_mail(self.id, True)
    
class WebsiteSupportTicketMessage(models.Model):

    _name = "website.support.ticket.message"
    
    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    content = fields.Text(string="Content")
   
class WebsiteSupportTicketCategories(models.Model):

    _name = "website.support.ticket.categories"
    
    name = fields.Char(required=True, translate=True, string='Category Name')
    cat_user_ids = fields.Many2many('res.users', string="Category Users")
   
class WebsiteSupportTicketStates(models.Model):

    _name = "website.support.ticket.states"
    
    name = fields.Char(required=True, translate=True, string='State Name')
    
class WebsiteSupportTicketUsers(models.Model):

    _inherit = "res.users"
    
    cat_user_ids = fields.Many2many('website.support.ticket.categories', string="Category Users")
    
class WebsiteSupportTicketCompose(models.Model):

    _name = "website.support.ticket.compose"

    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    partner_id = fields.Many2one('res.partner', string="Partner", readonly="True")
    email = fields.Char(string="Email", readonly="True")
    subject = fields.Char(string="Subject", readonly="True")
    body = fields.Html(string="Message Body")
    template_id = fields.Many2one('mail.template', string="Mail Template", domain="[('model_id','=','website.support.ticket')]")
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[self.ticket_id.id]                
            self.body = values['body']
            
    @api.one
    def send_reply(self):
        #Send email
        values = {}
        email_wrapper = self.env['ir.model.data'].get_object('website_support','support_ticket_reply_wrapper')
        values = email_wrapper.generate_email([self.id])[self.id]
        values['model'] = "website.support.ticket"
        values['res_id'] = self.ticket_id.id
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send()
        
        #(Depreciated) Add to message history field for back compatablity
        self.env['website.support.ticket.message'].create({'ticket_id': self.ticket_id.id, 'content':self.body.replace("<p>","").replace("</p>","")})
        
        #Post in message history
        self.ticket_id.message_post(body=self.body, subject=self.subject)
	staff_replied = self.env['ir.model.data'].get_object('website_support','website_ticket_state_staff_replied')
	self.ticket_id.state = staff_replied.id        