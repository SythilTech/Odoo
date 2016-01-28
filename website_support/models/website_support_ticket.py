# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteSupportTicket(models.Model):

    _name = "website.support.ticket"
    
    def _default_state(self):
        open_state = self.env['website.support.ticket.states'].search([('name','=','Open')])
        return open_state[0]
    
    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    person_name = fields.Char(required=True, string='Person Name', readonly=True)
    email = fields.Char(string="Email", readonly=True)
    category = fields.Many2one('website.support.ticket.categories', string="Category", required=True)
    subject = fields.Char(string="Subject", readonly=True)
    description = fields.Text(string="Description", readonly=True)
    state = fields.Many2one('website.support.ticket.states', required=True, default=_default_state, string="State")
    conversation_history = fields.One2many('website.support.ticket.message', 'ticket_id', string="Conversation History")

    @api.one
    def add_comment(self):
        """Adds a comment to the support ticket"""
        self.conversation_history.create({'content':self.add_comment})
        self.add_comment = ""
        #send email out to notify user of the comment
        #notification_template = self.env['ir.model.data'].get_object_reference('website_support', 'ticket_new_message')[1]        
	#values = self.env['mail.template'].generate_email(notification_template, self.id)
	#values['html_body'] += message.content + "<hr/>" + "<p>You can reply to this message here</p>"
	#msg_id = self.env['mail.mail'].create(values)
        #self.env['mail.mail'].send([msg_id], True)
    
class WebsiteSupportTicketMessage(models.Model):

    _name = "website.support.ticket.message"
    
    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    content = fields.Text(string="Content")
   
class WebsiteSupportTicketCategories(models.Model):

    _name = "website.support.ticket.categories"
    
    name = fields.Char(required=True, string='Category Name')
    cat_user_ids = fields.Many2many('res.users', string="Category Users")
   
class WebsiteSupportTicketStates(models.Model):

    _name = "website.support.ticket.states"
    
    name = fields.Char(required=True, string='State Name')
    
class WebsiteSupportTicketUsers(models.Model):

    _inherit = "res.users"
    
    cat_user_ids = fields.Many2many('website.support.ticket.categories', string="Category Users")