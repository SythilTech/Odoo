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

    @http.route('/support/subcategories/field/fetch', type='http', auth="public", website=True)
    def support_subcategories_field_fetch(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	            
	if values['subcategory'] != 'undefined':
	    sub_category_fields = request.env['website.support.ticket.subcategory.field'].sudo().search( [('wsts_id', '=', int(values['subcategory']) )])
	else:
	    return ""
	    
	#Only return a dropdown if this category has subcategories
	return_string = ""
	
	if sub_category_fields:
	    for sub_category_field in sub_category_fields:
            
	        return_string += "<div class=\"form-group\">\n"
	        return_string += "  <label class=\"col-md-3 col-sm-4 control-label\" for=\"efield_" + str(sub_category_field.id) + "\">" + sub_category_field.name + "</label>\n"
	        return_string += "  <div class=\"col-md-7 col-sm-8\">\n"

                if sub_category_field.type == "textbox":
                    return_string += "    <input type=\"text\" required=\"True\" class=\"form-control\" name=\"efield_" + str(sub_category_field.id) + "\">\n"
                elif sub_category_field.type == "polar":
                    return_string += "    <label class=\"radio-inline\">\n"
                    return_string += "      <input type=\"radio\" value=\"Yes\" name=\"efield_" + str(sub_category_field.id) + "\">Yes\n"
                    return_string += "    </label>\n"
                    return_string += "    <label class=\"radio-inline\">\n"
                    return_string += "      <input type=\"radio\" value=\"No\" name=\"efield_" + str(sub_category_field.id) + "\">No\n"
                    return_string += "    </label>\n"
                    
                return_string += "  </div>\n"
                return_string += "</div>\n"
            
        return return_string

    @http.route('/support/approve/<ticket_id>', type='http', auth="public", website=True)
    def support_approve(self, ticket_id, **kwargs):
        support_ticket = request.env['website.support.ticket'].browse( int(ticket_id) )

	awaiting_approval = request.env['ir.model.data'].get_object('website_support','awaiting_approval')
	
	if support_ticket.approval_id.id == awaiting_approval.id:
	    #Change the ticket state to approved
	    website_ticket_state_approval_accepted = request.env['ir.model.data'].get_object('website_support','website_ticket_state_approval_accepted')
	    support_ticket.state = website_ticket_state_approval_accepted.id
	
	    #Also change the approval
	    approval_accepted = request.env['ir.model.data'].get_object('website_support','approval_accepted')
	    support_ticket.approval_id = approval_accepted.id        

            return "Request Approved Successfully"
        else:
            return "Ticket does not need approval"
        
    @http.route('/support/disapprove/<ticket_id>', type='http', auth="public", website=True)
    def support_disapprove(self, ticket_id, **kwargs):
        support_ticket = request.env['website.support.ticket'].browse( int(ticket_id) )

	awaiting_approval = request.env['ir.model.data'].get_object('website_support','awaiting_approval')
	
	if support_ticket.approval_id.id == awaiting_approval.id:
	    #Change the ticket state to disapproved
	    website_ticket_state_approval_rejected = request.env['ir.model.data'].get_object('website_support','website_ticket_state_approval_rejected')
	    support_ticket.state = website_ticket_state_approval_rejected.id
	
	    #Also change the approval
	    approval_rejected = request.env['ir.model.data'].get_object('website_support','approval_rejected')
	    support_ticket.approval_id = approval_rejected.id
	
            return "Request Rejected Successfully"
        else:
            return "Ticket does not need approval"
            
    @http.route('/support/subcategories/fetch', type='http', auth="public", website=True)
    def support_subcategories_fetch(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	            
	sub_categories = request.env['website.support.ticket.subcategory'].sudo().search([('parent_category_id','=', int(values['category']) )])
	
	#Only return a dropdown if this category has subcategories
	return_string = ""
	
	if sub_categories:
	    return_string += "<div class=\"form-group\">\n"
	    return_string += "    <label class=\"col-md-3 col-sm-4 control-label\" for=\"subcategory\">Sub Category</label>\n"
	    return_string += "    <div class=\"col-md-7 col-sm-8\">\n"

            return_string += "        <select class=\"form-control\" id=\"subcategory\" name=\"subcategory\">\n"
            for sub_category in request.env['website.support.ticket.subcategory'].sudo().search([('parent_category_id','=', int(values['category']) )]):
                return_string += "            <option value=\"" + str(sub_category.id) + "\">" + sub_category.name.encode("utf-8") + "</option>\n"

            return_string += "        </select>\n"
	    return_string += "    </div>\n"
            return_string += "</div>\n"
            
        return return_string

    @http.route('/support/survey/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey(self, portal_key):
        """Display the survey"""

        support_ticket = request.env['website.support.ticket'].search([('portal_access_key','=', portal_key)])

        if support_ticket.support_rating:
            #TODO some security incase they guess the portal key of an incomplete survey
            return "Survey Already Complete"
        else:
            return http.request.render('website_support.support_ticket_survey_page', {'support_ticket': support_ticket})


    @http.route('/support/survey/process/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey_process(self, portal_key, **kw):
        """Insert Survey Response"""

        values = {}
 	for field_name, field_value in kw.items():
            values[field_name] = field_value

        support_ticket = request.env['website.support.ticket'].search([('portal_access_key','=', portal_key)])

        if support_ticket.support_rating:
            #TODO some security incase they guess the portal key of an incomplete survey
            return "Survey Already Complete"
        else:
            support_ticket.support_rating = values['rating']
            support_ticket.support_comment = values['comment']
            return http.request.render('website_support.support_survey_thank_you', {})

    @http.route('/support/account/create', type="http", auth="public", website=True)
    def support_account_create(self, **kw):
        """  Create no permission account"""
        
        setting_allow_user_signup = request.env['ir.values'].get_default('website.support.settings', 'allow_user_signup')

        if setting_allow_user_signup:
            return http.request.render('website_support.account_create', {})
        else:
            return "Account creation has been disabled"

    @http.route('/support/account/create/process', type="http", auth="public", website=True)
    def support_account_create_process(self, **kw):
        """  Create no permission account"""

        setting_allow_user_signup = request.env['ir.values'].get_default('website.support.settings', 'allow_user_signup')

        if setting_allow_user_signup:
 
            values = {}
	    for field_name, field_value in kw.items():
	        values[field_name] = field_value
	    
	    #Create the new user
	    new_user = request.env['res.users'].sudo().create({'name': values['name'], 'login': values['login'], 'email': values['login'], 'password': values['password'] })
	
	    #Remove all permissions
	    new_user.groups_id = False
	
	    #Add the user to the support group
	    support_group = request.env['ir.model.data'].sudo().get_object('website_support', 'support_group')
            support_group.users = [(4, new_user.id)]

	    #Also add them to the public group so they can access the website
	    public_group = request.env['ir.model.data'].sudo().get_object('base', 'group_public')
            public_group.users = [(4, new_user.id)]

            #Automatically sign the new user in
            request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	    request.session.authenticate(request.env.cr.dbname, values['login'], values['password'])

            #Redirect them to the support page
            return werkzeug.utils.redirect("/support/help")
        else:
            return "Account creation has been disabled"

    @http.route('/support/help', type="http", auth="public", website=True)
    def support_help(self, **kw):
        """Displays all help groups and thier child help pages"""

        permission_list = []
        for perm_group in request.env.user.groups_id:
            permission_list.append(perm_group.id)
        
        help_groups = http.request.env['website.support.help.groups'].sudo().search(['|', ('partner_ids', '=', False ), ('partner_ids', '=', request.env.user.partner_id.id ),'|', ('group_ids', '=', False ), ('group_ids', 'in', permission_list ), ('website_published','=',True)])

        setting_allow_user_signup = request.env['ir.values'].get_default('website.support.settings', 'allow_user_signup')
        
        manager = False
        if request.env['website.support.department.contact'].sudo().search_count([('user_id','=',request.env.user.id)]) == 1:
            manager = True
        
        return http.request.render('website_support.support_help_pages', {'help_groups': help_groups, 'setting_allow_user_signup': setting_allow_user_signup, 'manager': manager})

    @http.route('/support/ticket/reporting', type="http", auth="user", website=True)
    def support_ticket_reporting(self, **kw):
        """ Displays stats related to tickets in the department """
        
        #Just get the first department, managers in multiple departments are not supported
        department = request.env['website.support.department.contact'].search([('user_id','=',request.env.user.id)])[0].wsd_id

        extra_access = []
        for extra_permission in department.partner_ids:
            extra_access.append(extra_permission.id)
        
        support_tickets = http.request.env['website.support.ticket'].sudo().search(['|', ('partner_id','=',request.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False) ])        
        
        support_ticket_count = len(support_tickets)
                
        return http.request.render('website_support.support_ticket_reporting', {'department': department, 'support_ticket_count': support_ticket_count})
        
    @http.route('/support/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        """Let's public and registered user submit a support ticket"""
        person_name = ""
        if http.request.env.user.name != "Public user":
            person_name = http.request.env.user.name

        setting_max_ticket_attachments = request.env['ir.values'].get_default('website.support.settings', 'max_ticket_attachments')
        
        if setting_max_ticket_attachments == 0:
            #Back compatablity
            setting_max_ticket_attachments = 2
 
        setting_max_ticket_attachment_filesize = request.env['ir.values'].get_default('website.support.settings', 'max_ticket_attachment_filesize')

        if setting_max_ticket_attachment_filesize == 0:
            #Back compatablity
            setting_max_ticket_attachment_filesize = 500
            
        return http.request.render('website_support.support_submit_ticket', {'categories': http.request.env['website.support.ticket.categories'].sudo().search([]), 'person_name': person_name, 'email': http.request.env.user.email, 'setting_max_ticket_attachments': setting_max_ticket_attachments, 'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize})

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
        
        if "subcategory" in values:
            sub_category = values['subcategory']            
        else:
            sub_category = ""
            
        
        if http.request.env.user.name != "Public user":
            portal_access_key = randint(1000000000,2000000000)
            new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'],'category':values['category'], 'sub_category_id': sub_category, 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'partner_id':http.request.env.user.partner_id.id, 'attachment': my_attachment, 'attachment_filename': file_name, 'portal_access_key': portal_access_key})
            
            partner = http.request.env.user.partner_id
            
            #Add to the communication history
            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket", subject="New Support Ticket")
            
        else:
            search_partner = request.env['res.partner'].sudo().search([('email','=', values['email'] )])

            if len(search_partner) > 0:
                portal_access_key = randint(1000000000,2000000000)
                new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'], 'category':values['category'], 'sub_category_id': sub_category, 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name, 'partner_id':search_partner[0].id, 'portal_access_key': portal_access_key})
            else:
                portal_access_key = randint(1000000000,2000000000)
                new_ticket_id = request.env['website.support.ticket'].sudo().create({'person_name':values['person_name'], 'category':values['category'], 'sub_category_id': sub_category, 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name, 'portal_access_key': portal_access_key})

        #Remove the Administrator follower
        for ticket_follower in request.env['mail.followers'].sudo().search([('res_model','=','website.support.ticket'), ('res_id','=',new_ticket_id.id)]):
            ticket_follower.unlink()

        if "subcategory" in values:
            #Also get the data from the extra fields
            for extra_field in request.env['website.support.ticket.subcategory.field'].sudo().search([('wsts_id','=', int(sub_category) )]):
                if "efield_" + str(extra_field.id) in values:
                    request.env['website.support.ticket.field'].sudo().create({'wst_id': new_ticket_id.id, 'name': extra_field.name, 'value': values["efield_" + str(extra_field.id)] })
                else:
                    #All extra fields are required
                    return "Extra field is missing"
        
        if 'file' in values:

            for c_file in request.httprequest.files.getlist('file'):
                data = c_file.read()
                
                if c_file.filename:
                    request.env['ir.attachment'].sudo().create({
                        'name': c_file.filename,
                        'datas': data.encode('base64'),
                        'datas_fname': c_file.filename,
                        'res_model': 'website.support.ticket',
                        'res_id': new_ticket_id.id
                    })

        return werkzeug.utils.redirect("/support/ticket/thanks")
        
        
    @http.route('/support/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        """Displays a thank you page after the user submits a ticket"""
        return http.request.render('website_support.support_thank_you', {})

    @http.route('/support/ticket/view', type="http", auth="user", website=True)
    def support_ticket_view_list(self, **kw):
        """Displays a list of support tickets owned by the logged in user"""
        
        extra_access = []
        for extra_permission in http.request.env.user.partner_id.stp_ids:
            extra_access.append(extra_permission.id)
        
        support_tickets = http.request.env['website.support.ticket'].sudo().search(['|', ('partner_id','=',http.request.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('partner_id','!=',False) ])
        
        return http.request.render('website_support.support_ticket_view_list', {'support_tickets':support_tickets,'ticket_count':len(support_tickets)})

    @http.route('/support/ticket/view/<ticket>', type="http", auth="user", website=True)
    def support_ticket_view(self, ticket):
        """View an individual support ticket"""
        
        extra_access = []
        for extra_permission in http.request.env.user.partner_id.stp_ids:
            extra_access.append(extra_permission.id)
        
        #only let the user this ticket is assigned to view this ticket
        support_ticket = http.request.env['website.support.ticket'].sudo().search(['|', ('partner_id','=',http.request.env.user.partner_id.id), ('partner_id', 'in', extra_access), ('id','=',ticket) ])[0]
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket})

    @http.route('/support/portal/ticket/view/<portal_access_key>', type="http", auth="public", website=True)
    def support_portal_ticket_view(self, portal_access_key):
        """View an individual support ticket (portal access)"""
        
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('portal_access_key','=',portal_access_key) ])[0]
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket, 'portal_access_key': portal_access_key})

    @http.route('/support/portal/ticket/comment', type="http", auth="public", website=True)
    def support_portal_ticket_comment(self, **kw):
        """Adds a comment to the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('portal_access_key','=', values['portal_access_key'] ) ])[0]

        http.request.env['website.support.ticket.message'].create({'ticket_id':support_ticket.id, 'by': 'customer','content':values['comment']})
        
        support_ticket.state = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_replied')
            
        request.env['website.support.ticket'].sudo().browse(support_ticket.id).message_post(body=values['comment'], subject="Support Ticket Reply", message_type="comment")
        
        return werkzeug.utils.redirect("/support/portal/ticket/view/" + str(support_ticket.portal_access_key) )
        
    @http.route('/support/ticket/comment',type="http", auth="user")
    def support_ticket_comment(self, **kw):
        """Adds a comment to the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        ticket = http.request.env['website.support.ticket'].search([('id','=',values['ticket_id'])])
        
        #check if this user owns this ticket
        if ticket.partner_id.id == http.request.env.user.partner_id.id or ticket.partner_id in http.request.env.user.partner_id.stp_ids:

            http.request.env['website.support.ticket.message'].create({'ticket_id':ticket.id, 'by': 'customer','content':values['comment']})
            
            ticket.state = request.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_customer_replied')
            
            request.env['website.support.ticket'].sudo().browse(ticket.id).message_post(body=values['comment'], subject="Support Ticket Reply", message_type="comment")

        else:
            return "You do not have permission to submit this commment"
            
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
