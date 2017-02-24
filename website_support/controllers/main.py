# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
from random import randint
import os

import logging
_logger = logging.getLogger(__name__)

import openerp.http as http
from openerp.http import request

from openerp.addons.website.models.website import slug

class SupportTicketController(http.Controller):

    @http.route('/support/help', type="http", auth="public", website=True)
    def support_help(self, **kw):
        """Displays all help groups and thier child help pages"""
        return http.request.render('website_support.support_help_pages', {'help_groups': http.request.env['website.support.help.groups'].sudo().search([])})
        
    @http.route('/support/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        """Let's public and registered user submit a support ticket"""
        person_name = ""
        if http.request.env.user.name != "Public user":
            person_name = http.request.env.user.name
            
        return http.request.render('website_support.support_submit_ticket', {'categories': http.request.env['website.support.ticket.categories'].sudo().search([]), 'person_name': person_name, 'email': http.request.env.user.email})

    @http.route('/support/feedback/process/<help_page>', type="http", auth="public", website=True)
    def support_feedback(self, help_page, **kw):
        """Process user feedback"""
 
        values = {}
 	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        #Don't want them distorting the rating by submitting -50000 ratings
        if int(values['rating']) < 1 or int(values['rating']) > 5:
            return "Invalid rating"
           
        #Feeback is required
        if values['feedback'] == "":
            return "Feedback required"
        
        request.env['website.support.help.page.feedback'].sudo().create({'hp_id': int(help_page), 'feedback_rating': values['rating'], 'feedback_text': values['feedback'] })

        return werkzeug.utils.redirect("/support/help")

    @http.route('/helpgroup/new/<group>', type='http', auth="public", website=True)
    def help_group_create(self, group, **post):
        """Add new help group via content menu"""
        help_group = request.env['website.support.help.groups'].create({'name': group})
        return werkzeug.utils.redirect("/support/help")

    @http.route('/helppage/new', type='http', auth="public", website=True)
    def help_page_create(self, group_id, **post):
        """Add new help page via content menu"""
        help_page = request.env['website.support.help.page'].create({'group_id': group_id,'name': "New Help Page"})
        return werkzeug.utils.redirect("/support/help/%s/%s?enable_editor=1" % (slug(help_page.group_id), slug(help_page)))

    @http.route(['''/support/help/<model("website.support.help.groups"):help_group>/<model("website.support.help.page", "[('group_id','=',help_group[0])]"):help_page>'''], type='http', auth="public", website=True)
    def help_page(self, help_group, help_page, enable_editor=None, **post):
        """Displays help page template"""
        return http.request.render("website_support.help_page", {'help_page':help_page})


    @http.route('/support/ticket/process', type="http", auth="public", website=True, csrf=True)
    def support_process_ticket(self, **kwargs):
        """Adds the support ticket to the database and sends out emails to everyone following the support ticket category"""
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values['my_gold'] != "256":
            return "Bot Detected"
        
        my_attachment = ""
        file_name = ""
        if 'file' in values:
            my_attachment = base64.encodestring(values['file'].read() )
            file_name = values['file'].filename
            file_extension = os.path.splitext(file_name)[1]
            if file_extension == ".exe":
                return "exe files are not allowed"
        
        if http.request.env.user.name != "Public user":
            portal_access_key = randint(1000000000,2000000000)
            new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'],'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'partner_id':http.request.env.user.partner_id.id, 'attachment': my_attachment, 'attachment_filename': file_name, 'portal_access_key': portal_access_key})
            
            partner = http.request.env.user.partner_id
            
            #Add to the communication history
            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket", subject="New Support Ticket")
            
        else:
            search_partner = request.env['res.partner'].sudo().search([('email','=', values['email'] )])

            if len(search_partner) > 0:
                portal_access_key = randint(1000000000,2000000000)
                new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'], 'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name, 'partner_id':search_partner[0].id, 'portal_access_key': portal_access_key})
            else:
                portal_access_key = randint(1000000000,2000000000)
                new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'], 'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name, 'portal_access_key': portal_access_key})

        return werkzeug.utils.redirect("/support/ticket/thanks")
        
        
    @http.route('/support/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        """Displays a thank you page after the user submits a ticket"""
        return http.request.render('website_support.support_thank_you', {})

    @http.route('/support/ticket/view', type="http", auth="user", website=True)
    def support_ticket_view_list(self, **kw):
        """Displays a list of support tickets owned by the logged in user"""
        support_tickets = http.request.env['website.support.ticket'].sudo().search([('partner_id','=',http.request.env.user.partner_id.id)])
        return http.request.render('website_support.support_ticket_view_list', {'support_tickets':support_tickets,'ticket_count':len(support_tickets)})

    @http.route('/support/ticket/view/<ticket>', type="http", auth="user", website=True)
    def support_ticket_view(self, ticket):
        """View an individual support ticket"""
        #only let the user this ticket is assigned to view this ticket
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('partner_id','=',http.request.env.user.partner_id.id), ('id','=',ticket) ])[0]        
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket})

    @http.route('/support/portal/ticket/view/<portal_access_key>', type="http", auth="public", website=True)
    def support_portal_ticket_view(self, portal_access_key):
        """View an individual support ticket (portal access)"""
        
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('portal_access_key','=',portal_access_key) ])[0]
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket})

    @http.route('/support/ticket/comment',type="http", auth="user")
    def support_ticket_comment(self, **kw):
        """Adds a comment to the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        ticket = http.request.env['website.support.ticket'].search([('id','=',values['ticket_id'])])
        
        #check if this user owns this ticket
        if ticket.partner_id.id != http.request.env.user.partner_id.id:
            return "You do not have permission to submit this commment"
        else:
            http.request.env['website.support.ticket.message'].create({'ticket_id':ticket.id,'content':values['comment']})
            
            ticket.state = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_replied')
            
            request.env['website.support.ticket'].sudo().browse(ticket.id).message_post(body=values['comment'], subject="Support Ticket Reply", message_type="comment")
        
        return werkzeug.utils.redirect("/support/ticket/view/" + str(ticket.id))
        

    @http.route('/support/help/auto-complete',auth="public", website=True, type='http')
    def support_help_autocomplete(self, **kw):
        """Provides an autocomplete list of help pages"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        help_pages = request.env['website.support.help.page'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for help_page in help_pages:
            #return_item = {"label": help_page.name + "<br/><sub>" + help_page.group_id.name + "</sub>","value": help_page.url_generated}
            return_item = {"label": help_page.name,"value": help_page.url_generated}
            my_return.append(return_item) 
        
        return json.JSONEncoder().encode(my_return)
