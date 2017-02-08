# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from random import randint

import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)

import openerp.http as http
from openerp.http import request

class WebsiteDatingController(http.Controller):

    @http.route('/dating/notification/<notif>', type="http", auth="user", website=True)
    def dating_notification(self, notif, **kwargs):
        """Mark the notifaction as read and redirect"""
        
        notif = request.env['res.partner.dating.notification'].sudo().browse( int(notif) )
        
        #Stop them messing with other people's notifacations
        if request.env.user.partner_id.id == notif.partner_id.id:
            notif.has_read = True
            return werkzeug.utils.redirect(notif.ref_url)
        else:
            return "You do not own this notification"
        

    @http.route('/dating/profile/register', type="http", auth="public", website=True)
    def dating_profile_register(self, **kwargs):
        genders = request.env['res.partner.gender'].search([])
        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([('country_id','=', request.env.user.company_id.country_id.id)], order="name asc")
        #cities = request.env['res.country.state.city'].search([('state_id.country_id','=', request.env.user.company_id.country_id.id)])
        
        return http.request.render('website_dating.my_dating_register', {'genders': genders, 'countries': countries, 'states': states} )

    @http.route('/dating/profile/register/process', type="http", auth="public", website=True)
    def dating_profile_register_process(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
        date_of_birth = values['birth_date_year'] + "/" + values['birth_date_month'] + "/" + values['birth_date_day']

        d1 = datetime.strptime(date_of_birth, "%Y/%m/%d").date()
        d2 = date.today()
        age = relativedelta(d2, d1).years
	
	if age < request.env.user.company_id.min_dating_age:
	    return str(request.env.user.company_id.min_dating_age) + "+ Only"

	city = request.env['res.country.state.city'].sudo().search( [('state_id','=', int(values['state']) ), ('name','=ilike', values['city'] ) ] )
	
	if len(city) == 1:
	    city_id = city[0]
	else:
	    return str(len(city)) + " Can not find city with that name"
	    
	#city_id = request.env['res.country.state.city'].sudo().browse( int(values['city']) ) 
	
	#Create the new user
	new_user = request.env['res.users'].sudo().create({'name': values['first_name'] + " " + values['last_name'], 'login': values['email'], 'email': values['email'], 'password': values['password'] })
	
	#Add the user to the dating group
	dating_group = request.env['ir.model.data'].sudo().get_object('website_dating', 'dating_group')
        dating_group.users = [(4, new_user.id)]

        #Remove 'Contact Creation' permission        
	contact_creation_group = request.env['ir.model.data'].sudo().get_object('base', 'group_partner_manager')
        contact_creation_group.users = [(3,new_user.id)]

        #Also remove them as an employee
	human_resources_group = request.env['ir.model.data'].sudo().get_object('base', 'group_user')
        human_resources_group.users = [(3,new_user.id)]
        
        #Modify the users partner record
	new_user.partner_id.write({'dating': True, 'first_name': values['first_name'], 'last_name': values['last_name'], 'birth_date': date_of_birth, 'gender_id': values['gender'], 'profile_micro': values['self_description'], 'country_id': request.env.user.company_id.country_id.id, 'state_id': values['state'], 'city_id': city_id.id, 'city': city_id.name, 'image': base64.encodestring(values['file'].read()), 'privacy_setting': 'private', 'age': age })
            
        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])

        #Redirect them to the profile listing
        return werkzeug.utils.redirect("/dating/profiles")

    @http.route('/dating/local', type="http", auth="public", website=True)
    def dating_local_search(self):
        return http.request.render('website_dating.dating_search', {} )

    @http.route('/dating/local/<model("res.country.state"):state>/<model("res.country.state.city"):city>', type="http", auth="public", website=True)
    def dating_local(self, state, city):
        my_dates = request.env['res.partner'].sudo().search([('dating','=',True), ('state_id','=',state.id), ('city_id','=',city.id), ('privacy_setting','=','public')], limit=20, order="create_date desc")
        return http.request.render('website_dating.local_profile_list', {'my_dates': my_dates, 'state': state, 'city': city, 'my_dates_count': len(my_dates) } )
        
    @http.route('/dating/profiles', type="http", auth="user", website=True)
    def dating_list(self, **kwargs):
    
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value 
 
        my_dates = request.env.user.partner_id.get_dating_suggestions()
        my_dates_count = len(my_dates)
 
        dating_suggestions = []
        if my_dates_count > 0:
            for i in range(0, 20):
                rand_date = randint(1, len(my_dates) -1 )
                my_date =  my_dates[rand_date]
                dating_suggestions.append(my_date)
                
        return http.request.render('website_dating.my_dating_list', {'my_dates': dating_suggestions, 'my_dates_count': my_dates_count} )
        
    @http.route('/dating/auto-complete', auth="public", website=True, type='http')
    def dating_autocomplete(self, **kw):
        """Provides an autocomplete list of suburbs"""
        
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        #Get all businesses that match the search term
        suburbs = request.env['res.country.state.city'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for suburb in suburbs:
            return_item = {"label": suburb.name + "<br/><sub>" + suburb.state_id.name + ", " + suburb.state_id.country_id.name + "</sub>","value": "/dating/local/" + suburb.state_id.name.encode("UTF-8") + "-" + str(suburb.state_id.id) + "/" + suburb.name.encode("UTF-8") + "-" + str(suburb.id) }
            my_return.append(return_item)
        
        return json.JSONEncoder().encode(my_return)
