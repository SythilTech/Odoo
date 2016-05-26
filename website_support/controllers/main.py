# -*- coding: utf-8 -*-
import werkzeug
import json
import base64

import openerp.http as http
from openerp.http import request

from openerp.addons.website.models.website import slug

class MyController(http.Controller):

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
        return request.website.render("website_support.help_page", {'help_page':help_page})


    @http.route('/support/ticket/process', type="http", auth="public", website=True, csrf=False)
    def support_process_ticket(self, **kwargs):
        """Adds the support ticket to the database and sends out emails to everyone following the support ticket category"""
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        my_attachment = ""
        file_name = ""
        if 'file' in values:
            my_attachment = base64.encodestring(values['file'].read() )
            file_name = values['file'].filename
        
        if http.request.env.user.name != "Public user":
            new_ticket_id = request.env['website.support.ticket'].create({'person_name':values['person_name'],'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'partner_id':http.request.env.user.partner_id.id, 'attachment': my_attachment, 'attachment_filename': file_name})
            
            partner = http.request.env.user.partner_id
            
            #Add to the communication history
            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket", subject="New Support Ticket")
            
        else:
            new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'], 'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name})

        #send an email out to everyone in the category
        notification_template = request.env['ir.model.data'].sudo().get_object('website_support', 'new_support_ticket_category')
       	
        category = request.env['website.support.ticket.categories'].sudo().browse(int(values['category']))
        
        for my_user in category.cat_user_ids:
            notification_template.email_to = my_user.login
            notification_template.email_from = request.website.company_id.email
            notification_template.body_html = notification_template.body_html.replace("_ticket_url_", "web#id=" + str(new_ticket_id.id) + "&view_type=form&model=website.support.ticket")
            notification_template.send_mail(new_ticket_id.id, True)
            

        
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
        
        return werkzeug.utils.redirect("/support/ticket/view/" + str(ticket.id))
        

    @http.route('/support/help/auto-complete',auth="user", website=True, type='http')
    def support_help_autocomplete(self, **kw):
        """Broken but meant to provide an autocomplete list of help pages"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        help_pages = request.env['website.support.help.page'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for help_page in help_pages:
            return_item = {"label": help_page.name,"value": help_page.url}
            my_return.append(return_item) 
        
        return json.JSONEncoder().encode(my_return)
