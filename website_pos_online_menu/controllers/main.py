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