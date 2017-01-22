# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)

import openerp.http as http
from openerp.http import request

class WebsiteDatingController(http.Controller):

    @http.route('/dating/profile/register', type="http", auth="public", website=True)
    def dating_profile_register(self, **kwargs):
        genders = request.env['res.partner.gender'].search([])
        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([], order="name asc")
        cities = request.env['res.country.state.city'].search([])
        
        return http.request.render('website_dating.my_dating_register', {'genders': genders, 'countries': countries, 'states': states, 'cities': cities} )

    @http.route('/dating/profile/register/process', type="http", auth="public", website=True)
    def dating_profile_register_process(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
	city_id = request.env['res.country.state.city'].sudo().browse( int(values['city']) ) 
	
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

        date_of_birth = values['birth_date_year'] + "/" + values['birth_date_month'] + "/" + values['birth_date_day']
        
        #Modify the users partner record
	new_user.partner_id.write({'dating': True, 'first_name': values['first_name'], 'last_name': values['last_name'], 'birth_date': date_of_birth, 'gender_id': values['gender'], 'profile_micro': values['self_description'], 'country_id': values['country'], 'state_id': values['state'], 'city_id': city_id.id, 'city': city_id.name, 'image': base64.encodestring(values['file'].read()) })

        d1 = datetime.strptime(new_user.birth_date, "%Y-%m-%d").date()
        d2 = date.today()
        new_user.age = relativedelta(d2, d1).years
            
        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])

        #Redirect them to the profile listing
        return werkzeug.utils.redirect("/dating/profiles")
        
    @http.route('/dating/profiles', type="http", auth="user", website=True)
    def dating_list(self, **kwargs):
    
        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value 
 
        search_list = []
        return_dict = {}
        
        #only dating members
        search_list.append(('dating','=','True'))

        #exclude yourself from the list
        search_list.append(('id','!=', request.env.user.id))

        #opposite gender only
	male_gender = request.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        female_gender = request.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
        if request.env.user.partner_id.gender_id.id == male_gender.id:
            search_list.append(('gender_id','=', female_gender.id))
        elif request.env.user.partner_id.gender_id.id == female_gender.id:
            search_list.append(('gender_id','=', male_gender.id))    
        
        #min age preference
        min_age = request.env.user.partner_id.age - 5
        search_list.append(('age','>=', min_age))
        
        #max age preference
        max_age = request.env.user.partner_id.age + 5
        search_list.append(('age','<=', max_age))
        
        #Within 50km
        distance = 50
	mylon = float(request.env.user.partner_id.city_id.longitude)
	mylat = float(request.env.user.partner_id.city_id.latitude)
	dist = float(distance) * 0.621371
	lon_min = mylon-dist/abs(math.cos(math.radians(mylat))*69);
	lon_max = mylon+dist/abs(math.cos(math.radians(mylat))*69);
	lat_min = mylat-(dist/69);
	lat_max = mylat+(dist/69);
        search_list.append(('city_id.longitude','>=',lon_min))
        search_list.append(('city_id.longitude','<=',lon_max))
        search_list.append(('city_id.latitude','<=',lat_min))
        search_list.append(('city_id.latitude','>=',lat_max))
            
        my_dates = http.request.env['res.partner'].sudo().search(search_list, limit=15)
        my_dates_count = len(my_dates)
        
        return http.request.render('website_dating.my_dating_list', {'my_dates': my_dates, 'my_dates_count': my_dates_count} )