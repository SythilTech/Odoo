import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import base64
import logging
_logger = logging.getLogger(__name__)
import werkzeug
from datetime import datetime
import json
from openerp.addons.website.models.website import slug

class MyController(http.Controller):

    @http.route('/support/help', type="http", auth="public", website=True)
    def support_help(self, **kw):
        return http.request.render('website_support.support_help_pages', {'help_groups': http.request.env['website.support.help.groups'].sudo().search([])})
        
    @http.route('/support/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        return http.request.render('website_support.support_submit_ticket', {'categories': http.request.env['website.support.ticket.categories'].sudo().search([]), 'person_name': http.request.env.user.name, 'email': http.request.env.user.email})


    @http.route('/support/ticket/process', type="http", auth="public", website=True)
    def support_process_ticket(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        my_attachment = base64.encodestring(values['file'].read() )
        
        if http.request.env.user.id:
            new_ticket_id = request.env['website.support.ticket'].create({'person_name':values['person_name'],'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'partner_id':http.request.env.user.partner_id.id, 'attachment': my_attachment, 'attachment_filename': values['file'].filename})
            
            partner = http.request.env.user.partner_id
            
            #Add to the communication history
            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket", subject="New Support Ticket")
            
        else:
            new_ticket_id = request.env['website.support.ticket'].create({'person_name':values['person_name'],'category':values['category'], 'email':values['email'], 'description':values['description'], 'subject':values['subject'], 'attachment': my_attachment, 'attachment_filename': values['file'].filename})

        #send an email out to everyone in the category
        notification_template = request.env['ir.model.data'].get_object('website_support', 'new_support_ticket_category')
       	
        category = request.env['website.support.ticket.categories'].sudo().browse(int(values['category']))
        
        for my_user in category.cat_user_ids:
            values = request.env['email.template'].generate_email(notification_template.id, new_ticket_id.id)
       	    values['email_to'] = my_user.login
            values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(new_ticket_id.id) + "&view_type=form&model=website.support.ticket")
       	    
       	    msg_id = request.env['mail.mail'].create(values)
            
        request.env['mail.mail'].process_email_queue()
        
        return werkzeug.utils.redirect("/support/ticket/thanks")
        
        
    @http.route('/support/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        return http.request.render('website_support.support_thank_you', {})

    @http.route('/support/ticket/view', type="http", auth="user", website=True)
    def support_ticket_view_list(self, **kw):
        #Only show tickets from this user
        support_tickets = http.request.env['website.support.ticket'].sudo().search([('partner_id','=',http.request.env.user.partner_id.id)])
        return http.request.render('website_support.support_ticket_view_list', {'support_tickets':support_tickets,'ticket_count':len(support_tickets)})

    @http.route('/support/ticket/view/<ticket>', type="http", auth="user", website=True)
    def support_ticket_view(self, ticket):
        #only let the user this ticket is assigned to view this ticket
        support_ticket = http.request.env['website.support.ticket'].sudo().search([('partner_id','=',http.request.env.user.partner_id.id), ('id','=',ticket) ])[0]        
        return http.request.render('website_support.support_ticket_view', {'support_ticket':support_ticket})

    @http.route('/helpgroup/new/<group>', type='http', auth="public", website=True)
    def help_group_create(self, group, **post):
        help_group = request.env['website.support.help.groups'].create({'name': group})
        return werkzeug.utils.redirect("/support/help")

    @http.route('/helppage/new', type='http', auth="public", website=True)
    def help_page_create(self, group_id, **post):
        help_page = request.env['website.support.help.page'].create({'group_id': group_id,'name': "New Help Page"})
        return werkzeug.utils.redirect("/support/help/%s/%s?enable_editor=1" % (slug(help_page.group_id), slug(help_page)))

    @http.route(['''/support/help/<model("website.support.help.groups"):help_group>/<model("website.support.help.page", "[('group_id','=',help_group[0])]"):help_page>'''], type='http', auth="public", website=True)
    def help_page(self, help_group, help_page, enable_editor=None, **post):
        return request.website.render("website_support.help_page", {'help_page':help_page})

    @http.route('/support/ticket/comment',type="http", auth="user")
    def support_ticket_comment(self, **kw):

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
