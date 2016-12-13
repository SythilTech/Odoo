# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)
from openerp.addons.website.models.website import slug

import openerp.http as http
from openerp.http import request

class OnlineMenuController(http.Controller):

    @http.route('/restaurant/menu', type="http", auth="public", website=True)
    def restaurant_menu(self, **kwargs):
        pos_categories = request.env['pos.category'].sudo().search([])
        return http.request.render('website_pos_online_menu.online_menu', {'pos_categories': pos_categories} )

    @http.route('/restaurant/order/update', type='json', auth="public", website=True, csrf=False)
    def restaurant_menu_order_update(self, product_id):
        if 'pos_menu_order_id' not in request.session:
            website_pos_order = request.env['website.pos.order'].sudo().create({'state': 'draft', 'type': 'delivery'})
            request.env['website.pos.order.line'].sudo().create({'wpo_id': website_pos_order.id, 'product_id': product_id, 'quantity': 1})
            request.session['pos_menu_order_id'] = website_pos_order.id
        else:
            website_pos_order = request.env['website.pos.order'].sudo().browse( request.session['pos_menu_order_id'] )
            
            #Check if the product has already been added to the order
            order_line = request.env['website.pos.order.line'].sudo().search([('wpo_id','=', website_pos_order.id), ('product_id', '=', product_id) ])
            if len(order_line) > 0:
                order_line.quantity += 1
            else:
                request.env['website.pos.order.line'].sudo().create({'wpo_id': website_pos_order.id, 'product_id': product_id, 'quantity': 1})           

        return True
        
    @http.route('/restaurant/checkout', type="http", auth="public", website=True)
    def restaurant_menu_checkout(self, **kwargs):
        website_pos_order = request.env['website.pos.order'].sudo().browse( request.session['pos_menu_order_id'] )
        return http.request.render('website_pos_online_menu.online_menu_checkout', {'website_pos_order': website_pos_order} )