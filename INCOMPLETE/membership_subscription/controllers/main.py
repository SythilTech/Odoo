# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)
import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

class MembershipSubscriptionController(http.Controller):

    @http.route('/membership/cancel', type="http", auth="user", website=True)
    def membership_cancel(self):
    
        #Remove the membership assignment
        request.env.user.partner_id.payment_membership_id = False

        #Remove all permissions
        request.env.user.groups_id = False

        #Also add them to the portal group so they can access the website
        group_portal = request.env['ir.model.data'].sudo().get_object('base','group_portal')
        group_portal.users = [(4, request.env.user.id)]

        return werkzeug.utils.redirect("/")

    @http.route('/membership/management', type="http", auth="user", website=True)
    def membership_management(self):
        return request.render('membership_subscription.membership_management', {'current_membership': request.env.user.partner_id.payment_membership_id})

    @http.route('/membership/signup/thank-you', type="http", auth="user", website=True)
    def membership_signup_thankyou(self):
        return request.render('membership_subscription.signup_thank_you', {})

    @http.route('/membership/signup/<model("payment.membership"):membership>', type="http", auth="public", website=True)
    def membership_signup(self, membership):
        return request.render('membership_subscription.signup_form', {'membership': membership})

    @http.route('/membership/signup/process', type="http", auth="public")
    def membership_signup_process(self, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        membership = request.env['payment.membership'].sudo().browse( int(values['membership_id']) )

        #Create the new user
        new_user = request.env['res.users'].sudo().create({'name': values['name'], 'login': values['email'], 'email': values['email'], 'password': values['password'] })

        #Remove all permissions
        new_user.groups_id = False

        #Also add them to the portal group so they can access the website
        group_portal = request.env['ir.model.data'].sudo().get_object('base','group_portal')
        group_portal.users = [(4, new_user.id)]
            
        #Add the user to the assigned groups
        for user_group in membership.group_ids:
            user_group.users = [(4, new_user.id)]

        #Modify the users partner record only with the allowed fields
        extra_fields_dict = {}
        for extra_field in membership.extra_field_ids:
            extra_fields_dict[extra_field.sudo().field_id.name] = values[extra_field.name]

        #Add them to the membership
        extra_fields_dict['payment_membership_id'] = membership.id

        new_user.partner_id.write(extra_fields_dict)

        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])

        #Redirect them
        return werkzeug.utils.redirect(membership.redirect_url)