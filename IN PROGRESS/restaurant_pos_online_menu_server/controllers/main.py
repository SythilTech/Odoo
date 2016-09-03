import openerp.http as http
from openerp.http import request
import logging
import json
from datetime import datetime
_logger = logging.getLogger(__name__)

class TakeawayController(http.Controller):

    @http.route('/takeaway', auth='public', website=True)
    def takeaway_search(self):
        return http.request.render('restaurant_pos_online_menu_server.takeaway_search', {})

    @http.route('/takeaway/search/autocomplete',auth="public", website=True, type='http')
    def takeaway_search_autocomplete(self, **kw):
        """Autocomplete list of suburbs"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        suburbs = request.env['res.better.zip'].sudo().search([('city','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for suburb in suburbs:
            return_item = {"label": suburb.city,"value": "/takeaway/" + suburb.country_id.name + "/" + suburb.state_id.name + "/" + suburb.city}
            my_return.append(return_item) 
        
        return json.JSONEncoder().encode(my_return)
        
    @http.route('/takeaway/<country>', auth='public', website=True)
    def takeaway_states(self, country):
        states = http.request.env['res.country.state'].sudo().search([('country_id.name','=',country)])
        return http.request.render('restaurant_pos_online_menu_server.takeaway_states', {'country': country,'states':states})


    @http.route('/takeaway/<country>/<state>', auth='public', website=True)
    def takeaway_suburbs(self, country, state):
        suburbs = http.request.env['res.better.zip'].sudo().search([('country_id.name','=',country),('state_id.name','=',state)])
        return http.request.render('restaurant_pos_online_menu_server.takeaway_suburbs', {'country':country, 'state':state, 'suburbs': suburbs})

    @http.route('/takeaway/<country>/<state>/<suburb>', type="http", auth="public", website=True)
    def takeaway_restaurants(self, country, state, suburb):
        my_suburb = http.request.env['res.better.zip'].sudo().search([('country_id.name','=',country),('state_id.name','=',state),('city','=',suburb)])[0]
        
        #Get a list of restaurants that deliver to this suburb
        
        restaurants = http.request.env['takeaway.restaurant'].sudo().search([('delivary_suburbs', '=', my_suburb.id)])
        
        return http.request.render('restaurant_pos_online_menu_server.takeaway_restaurant_list', {'restaurants': restaurants})

    
    @http.route('/takeaway/<country>/<state>/<suburb>/<restaurant>', type="http", auth="public", website=True)
    def takeaway_restaurant_products(self, country, state, suburb, restaurant):
        restaurant = http.request.env['takeaway.restaurant'].sudo().search([('location_id.country_id.name', '=', country), ('location_id.state_id.name', '=', state), ('location_id.city', '=', suburb), ('slug', '=', restaurant)])
        
        return http.request.render('restaurant_pos_online_menu_server.takeaway_product_list', {'restaurant': restaurant})
