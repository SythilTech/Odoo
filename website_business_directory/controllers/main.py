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

class WebsiteBusinessDiretoryController(http.Controller):

    @http.route('/directory', type="http", auth="public", website=True)
    def directory_search(self, **kwargs):
        privacy_mode = request.env['ir.values'].get_default('website.directory.settings', 'privacy_mode')
        
        if privacy_mode == "private":
            return werkzeug.utils.redirect("/directory/register")
        else:
            listings = request.env['res.partner'].sudo().search([('in_directory','=', True)])
            categories = request.env['res.partner.directory.category'].sudo().search([])
            return http.request.render('website_business_directory.directory_search', {'listings':listings, 'categories':categories} )        

    @http.route('/directory/register', type="http", auth="public", website=True)
    def directory_register(self, **kwargs):
        if request.env.user == request.website.user_id:
            return http.request.render('website_business_directory.directory_register', {} )
        else:
            return werkzeug.utils.redirect("/directory/account")            

    @http.route('/directory/register/process', type="http", auth="public", website=True)
    def directory_register_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
	#Create the new user
	new_user = request.env['res.users'].sudo().create({'name': values['name'], 'login': values['email'], 'email': values['email'], 'password': values['password'] })
	
	#Add the user to the business directory group
	dating_group = request.env['ir.model.data'].sudo().get_object('website_business_directory', 'directory_group')
        dating_group.users = [(4, new_user.id)]

        #Remove 'Contact Creation' permission        
	contact_creation_group = request.env['ir.model.data'].sudo().get_object('base', 'group_partner_manager')
        contact_creation_group.users = [(3,new_user.id)]

        #Also remove them as an employee
	human_resources_group = request.env['ir.model.data'].sudo().get_object('base', 'group_user')
        human_resources_group.users = [(3,new_user.id)]

        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])

        #Redirect them to thier account page
        return werkzeug.utils.redirect("/directory/account")

    @http.route('/directory/account', type='http', auth="user", website=True)
    def directory_account(self, **kwargs):
        businesses = request.env['res.partner'].sudo().search([('in_directory','=', True), ('business_owner','=', request.env.user.id)])
        return http.request.render('website_business_directory.directory_account', {'businesses': businesses} )

    @http.route('/directory/account/business/edit/<model("res.partner"):directory_company>', type='http', auth="user", website=True)
    def directory_account_business_edit(self, directory_company, **kwargs):
        if directory_company.in_directory and directory_company.business_owner.id == request.env.user.id:
            countries = request.env['res.country'].search([])
            states = request.env['res.country.state'].search([])
            directory_categories = request.env['res.partner.directory.category'].sudo().search([('parent_category','=',False)])
            return http.request.render('website_business_directory.directory_account_business_edit', {'directory_company': directory_company, 'countries': countries,'states': states, 'directory_categories': directory_categories} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/account/business/stats/<model("res.partner"):directory_company>', type='http', auth="user", website=True)
    def directory_account_business_stats(self, directory_company, **kwargs):
        if directory_company.in_directory and directory_company.business_owner.id == request.env.user.id:
            stats = request.env['website.directory.stat'].sudo().search([('listing_id', '=', directory_company.id)])
            return http.request.render('website_business_directory.directory_account_business_stats', {'stats': stats} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/account/business/add', type='http', auth="user", website=True)
    def directory_account_business_add(self, **kwargs):
        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([])
        directory_categories = request.env['res.partner.directory.category'].sudo().search([('parent_category','=',False)])
        
        form_string = ""
        
        for extra_field in request.env['website.directory.field'].sudo().search([]):
            method = '_generate_html_%s' % (extra_field.field_type.internal_type,)
	    action = getattr(self, method, None)
	    	        
	    if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	    form_string += action(extra_field)
                
        return http.request.render('website_business_directory.directory_account_business_add', {'countries': countries,'states': states, 'directory_categories':directory_categories, 'form_string':form_string} )

    @http.route('/directory/account/business/add/process', type='http', auth="user", website=True)
    def directory_account_business_add_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        business_logo = base64.encodestring(values['logo'].read() )                
        
        insert_values = {'business_owner': request.env.user.id, 'in_directory': True, 'name': values['name']}

        #Only add fields in allowed field list
        for extra_field in request.env['website.directory.field'].sudo().search([]):
            if extra_field.field_id.name in values:
                insert_values[extra_field.field_id.name] = values[extra_field.field_id.name]

        categories = []
        for category in request.env['res.partner.directory.category'].sudo().search([]):
            if "category_" + str(category.id) in values:
                categories.append(category.id)
                
        insert_values['company_category_ids'] = [(6, 0, categories)]
        if 'email' in values: insert_values['email'] = values['email']
        if 'street' in values: insert_values['street'] = values['street']
        if 'city' in values: insert_values['city'] = values['city']
        if 'state_id' in values: insert_values['state_id'] = values['state_id']
        if 'country_id' in values: insert_values['country_id'] = values['country_id']
        if 'zip' in values: insert_values['zip'] = values['zip']
        if 'directory_description' in values: insert_values['directory_description'] = values['directory_description']
        if 'allow_restaurant_booking' in values: insert_values['allow_restaurant_booking'] = True
        insert_values['image'] =  business_logo
            
        new_listing = request.env['res.partner'].sudo().create(insert_values)

        if 'monday_start' in values and 'monday_end' in values:
            start_time = values['monday_start']
            end_time = values['monday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '0', 'start_time': start_time, 'end_time': end_time})

        if 'tuesday_start' in values and 'tuesday_end' in values:
            start_time = values['tuesday_start']
            end_time = values['tuesday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '1', 'start_time': start_time, 'end_time': end_time})

        if 'wednesday_start' in values and 'wednesday_end' in values:
            start_time = values['wednesday_start']
            end_time = values['wednesday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '2', 'start_time': start_time, 'end_time': end_time})

        if 'thursday_start' in values and 'thursday_end' in values:
            start_time = values['thursday_start']
            end_time = values['thursday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '3', 'start_time': start_time, 'end_time': end_time})

        if 'friday_start' in values and 'friday_end' in values:
            start_time = values['friday_start']
            end_time = values['friday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '4', 'start_time': start_time, 'end_time': end_time})

        if 'saturday_start' in values and 'saturday_end' in values:
            start_time = values['saturday_start']
            end_time = values['saturday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '5', 'start_time': start_time, 'end_time': end_time})

        if 'sunday_start' in values and 'sunday_end' in values:
            start_time = values['sunday_start']
            end_time = values['sunday_end']
            request.env['website.directory.timeslot'].sudo().create({'business_id': new_listing.id, 'day': '6', 'start_time': start_time, 'end_time': end_time})

        #Redirect them to thier account page
        return werkzeug.utils.redirect("/directory/account")

    @http.route('/directory/account/business/edit/process', type='http', auth="user", website=True)
    def directory_account_business_edit_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        business_logo = base64.encodestring(values['logo'].read() )

        existing_record = request.env['res.partner'].browse( int(values['business_id'] ) )
        
        if existing_record.in_directory and existing_record.business_owner.id == request.env.user.id:
            updated_listing = existing_record.sudo().write({'name': values['name'], 'email': values['email'], 'street': values['street'], 'city': values['city'], 'state_id': values['state'], 'country_id': values['country'], 'zip': values['zip'], 'directory_description': values['description'], 'directory_monday_start': values['directory_monday_start'], 'directory_monday_end': values['directory_monday_end'], 'directory_tuesday_start': values['directory_tuesday_start'], 'directory_tuesday_end': values['directory_tuesday_end'], 'directory_wednbesday_start': values['directory_wednesday_start'], 'directory_wednbesday_end': values['directory_wednesday_end'], 'directory_thursday_start': values['directory_thursday_start'], 'directory_thursday_end': values['directory_thursday_end'], 'directory_friday_start': values['directory_friday_start'], 'directory_friday_end': values['directory_friday_end'], 'directory_saturday_start': values['directory_saturday_start'], 'directory_saturday_end': values['directory_saturday_end'], 'directory_sunday_start': values['directory_sunday_start'], 'directory_sunday_end': values['directory_sunday_end'], 'allow_restaurant_booking': values['allow_restaurant_booking'], 'image': business_logo })

            #Redirect them to thier account page
            return werkzeug.utils.redirect("/directory/account")
        else:
            return "Permission Denied"

    @http.route('/directory/review/process', type='http', auth="public", website=True)
    def directory_review_process(self, **kwargs):
        
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        directory_company = request.env['res.partner'].sudo().browse( int(values['business_id']) )        
        
        if directory_company.in_directory:
            if int(values['rating']) >= 1 and int(values['rating']) <= 5:            
                new_review = request.env['res.partner.directory.review'].sudo().create({'business_id': values['business_id'], 'name': values['name'], 'description': values['description'], 'rating': values['rating'] })

                #Send email
                notification_template = request.env['ir.model.data'].sudo().get_object('website_business_directory', 'review_submitted')
                notification_template.send_mail(new_review.id, True)

                return werkzeug.utils.redirect("/directory/company/" + slug(directory_company) )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>', type='http', auth="public", website=True)
    def directory_company_page(self, directory_company, **kwargs):
        privacy_mode = request.env['ir.values'].get_default('website.directory.settings', 'privacy_mode')
        
        if privacy_mode == "private":
	    return werkzeug.utils.redirect("/directory/register")
        else:
            if directory_company.in_directory:
            
                ref = ""
            	if "Referer" in request.httprequest.headers:
	    	    ref = request.httprequest.headers['Referer']

                isocountry = request.session.geoip and request.session.geoip.get('country_code') or False
                request.env['website.directory.stat'].sudo().create({'listing_id': directory_company.id, 'ref':ref, 'ip': request.httprequest.remote_addr, 'location': isocountry})
                return http.request.render('website_business_directory.directory_company_page', {'directory_company': directory_company, 'image_count': len(directory_company.directory_images) } )
            else:
                return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>/booking', type='http', auth="public", website=True)
    def directory_company_booking(self, directory_company, **kwargs):
        if directory_company.in_directory:
            return http.request.render('website_business_directory.directory_company_booking', {'directory_company': directory_company} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>/menu', type='http', auth="public", website=True)
    def directory_company_menu(self, directory_company, **kwargs):
        if directory_company.in_directory:
            return http.request.render('website_business_directory.directory_company_menu', {'directory_company': directory_company} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/booking/process', type='http', auth="public", website=True)
    def directory_company_booking_process(self, **kwargs):
        """Insert the booking into the database then notify the restaurant of the booking via thier preferred notification method(email only atm)"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        directory_company = request.env['res.partner'].sudo().browse( int(values['business_id']) )
        
        if directory_company.allow_restaurant_booking:
            new_booking = request.env['website.directory.booking'].sudo().create({'partner_id': values['business_id'], 'booking_name': values['booking_name'], 'email': values['email'], 'number_of_people': values['number_of_people'], 'booking_datetime': values['booking_datetime'], 'notes': values['notes']})
        
            #Send email
            notification_template = request.env['ir.model.data'].sudo().get_object('website_business_directory', 'directory_booking')
            notification_template.send_mail(new_booking.id, True)
            
            return werkzeug.utils.redirect("/directory")
        else:
            return "BOOKINGS NOT ALLOWED"

    @http.route('/directory/search/<search_string>', type="http", auth="public", website=True)
    def directory_search_results(self, search_string, **kwargs):
        privacy_mode = request.env['ir.values'].get_default('website.directory.settings', 'privacy_mode')
        
        if privacy_mode == "private":
            return werkzeug.utils.redirect("/directory/register")
        else:
            directory_companies = request.env['res.partner'].sudo().search([('in_directory','=', True), '|', ('name','ilike', search_string), ('company_category_ids','=', search_string) ])
            return http.request.render('website_business_directory.directory_search_results', {'directory_companies': directory_companies} )

    @http.route('/directory/categories', type="http", auth="public", website=True)
    def directory_categories(self, **kwargs):
        privacy_mode = request.env['ir.values'].get_default('website.directory.settings', 'privacy_mode')
        
        if privacy_mode == "private":
            return werkzeug.utils.redirect("/directory/register")
        else:
            directory_categories = request.env['res.partner.directory.category'].sudo().search([('parent_category','=',False)])
            return http.request.render('website_business_directory.directory_categories', {'directory_categories': directory_categories} )
        
    @http.route('/directory/auto-complete',auth="public", website=True, type='http')
    def directory_autocomplete(self, **kw):
        """Provides an autocomplete list of businesses and typs in the directory"""
        
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        #Get all businesses that match the search term
        directory_partners = request.env['res.partner'].sudo().search([('in_directory','=',True), ('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for directory_partner in directory_partners:
            return_item = {"label": directory_partner.name + "<br/><sub>" + directory_partner.street + "</sub>","value": "/directory/search/" + directory_partner.name}
            my_return.append(return_item)

        #Get all business types that match the search term
        directory_categories = request.env['res.partner.directory.category'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for directory_category in directory_categories:
            return_item = {"label": directory_category.name,"value": "/directory/search/" + directory_category.name }
            my_return.append(return_item)
        
        return json.JSONEncoder().encode(my_return)

    def _generate_html_textbox(self, field):
        """Generate textbox HTML"""
        html_output = ""        
        html_output += "<div class=\"form-group\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.field_id.name.encode("utf-8") + "\">" + field.field_id.field_description.encode("utf-8") + "</label>\n"	    
	html_output += "  <input type=\"text\" class=\"form-control\" name=\"" + field.field_id.name.encode("utf-8") + "\""
		                                    
	if field.field_id.required == True:
	    html_output += " required=\"required\""
		
	if field.field_id.size > 0:
	    html_output += ' maxlength="' + str(field.field_id.size) + '"'
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output