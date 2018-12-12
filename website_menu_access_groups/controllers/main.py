# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)
import werkzeug

import odoo.http as http
from odoo.http import request

class WebsiteMenuAccessGRoupsController(http.Controller):

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