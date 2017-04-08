import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    @http.route('/shop/cart/instantcheckout', type="http", auth="public", website=True)
    def shop_cart_instantcheckout(self, **kwargs):
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        #get the http POST/GET product_id
        product_id = values['product_id']
        
        #Add the item to the cart(no redirect)
        request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=1, set_qty=0)
        
        return request.redirect("/shop/checkout")