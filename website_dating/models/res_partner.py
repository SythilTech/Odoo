# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import math
import logging
_logger = logging.getLogger(__name__)
from random import randint

from openerp import api, fields, models

class ResPartnerWebsiteDating(models.Model):

    _inherit = "res.partner"

    dating = fields.Boolean(string="Dating")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    fake_profile = fields.Boolean(string="Fake Profile")
    birth_date = fields.Date("Birth Date")
    age = fields.Integer(string="Age")
    city_id = fields.Many2one('res.country.state.city', string="City")
    gender_id = fields.Many2one('res.partner.gender', string="Gender")
    profile_micro = fields.Char(size=100, string="Profile Micro Summary")
    setting_email_suggestion = fields.Boolean(string="Email Suggestions", default="True")
    privacy_setting = fields.Selection([('public','Public'), ('private','Private')], string="Privacy Setting")    
        
    @api.onchange('birth_date')
    def _onchange_birth_date(self):
        """Updates age when DOB is changed"""
        if self.birth_date:
            d1 = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
            
    @api.model
    def update_ages(self):
        """Updates the ages of all partners in the database once a day"""
        for rec in self.env['res.partner'].search([]):
            if rec.birth_date:
                d1 = datetime.strptime(rec.birth_date, "%Y-%m-%d").date()
                d2 = date.today()
                rec.age = relativedelta(d2, d1).years

    @api.model
    def create_fake_dating_profiles(self, country_id, state_id, num_profiles, min_age, max_age):
        """Create a large amount of fake profile to aid in testing of dating algorithm"""
                
        calc_min_days = 365 * min_age
        calc_max_days = 365 * max_age
                
        my_delta_young_time = datetime.utcnow() - timedelta(days=calc_min_days)
        my_delta_old_time = datetime.utcnow() - timedelta(days=calc_max_days)	        

        suburb_list = state_id.city_ids

        male_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        female_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
        
        for i in range(0, num_profiles):
	    partner_dict = {'dating':'True', 'fake_profile':'True', 'setting_email_suggestion': False, 'privacy_setting': 'public'}
	    
	    #Random name
	    first_name = self.env['res.dating.fake.first'].browse( randint(1, 4999) )
	    last_name = self.env['res.dating.fake.last'].browse( randint(1, 4999) )
            partner_dict['first_name'] = first_name.name
            partner_dict['last_name'] = last_name.name
            partner_dict['name'] = first_name.name + " " + last_name.name
            
            #Random gender
            partner_dict['gender_id'] = first_name.gender_id.id
            
            #Random age
            birth_date = my_delta_old_time + timedelta(seconds=randint(0, int((my_delta_young_time - my_delta_old_time).total_seconds())))
            age = relativedelta(date.today(), birth_date).years
	    partner_dict['birth_date'] = birth_date
            partner_dict['age'] = age
            
            #Random Location (within state)
            rand_suburb = suburb_list[randint(0, len(suburb_list) - 1)]
            partner_dict['country_id'] = rand_suburb.state_id.country_id.id
            partner_dict['state_id'] = rand_suburb.state_id.id
            partner_dict['city_id'] = rand_suburb.id
            partner_dict['city'] = rand_suburb.name
            
            #Random profile text
            partner_dict['profile_micro'] = "I am " + str(age) + " year old " + first_name.gender_id.name.lower() + " looking for a relationship."

            #Execute all the fake profile creation systems
            for match_sytem in self.env['res.dating.matching'].sudo().search([]):
             
                method = '_dating_fake_action_%s' % (match_sytem.match_name,)
 	        action = getattr(self, method, None)
 	        
 	        if not action:
                    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
 	
 	        #Call the submit action, passing the action settings and the history object
                partner_dict = action(partner_dict)

            
            #Create the partner
            new_partner = self.env['res.partner'].create(partner_dict)

    def get_dating_suggestions(self):
        search_list = []
        
        #only dating members
        search_list.append(('dating','=','True'))

        #exclude yourself from the list
        search_list.append(('id','!=', self.id))

        #opposite gender only
	male_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        female_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
        if self.gender_id.id == male_gender.id:
            search_list.append(('gender_id','=', female_gender.id))
        elif self.gender_id.id == female_gender.id:
            search_list.append(('gender_id','=', male_gender.id))

        #min age preference
        min_age = self.age - 5
        search_list.append(('age','>=', min_age))
            
        #max age preference
        max_age = self.age + 5
        search_list.append(('age','<=', max_age))
            
        #Within 20km
        distance = 20
	mylon = float(self.city_id.longitude)
	mylat = float(self.city_id.latitude)
	dist = float(distance) * 0.621371
	lon_min = mylon-dist/abs(math.cos(math.radians(mylat))*69);
	lon_max = mylon+dist/abs(math.cos(math.radians(mylat))*69);
	lat_min = mylat-(dist/69);
	lat_max = mylat+(dist/69);
        search_list.append(('city_id.longitude','>=',lon_min))
        search_list.append(('city_id.longitude','<=',lon_max))
        search_list.append(('city_id.latitude','<=',lat_min))
        search_list.append(('city_id.latitude','>=',lat_max))

        #Execute all the matching systems
        for match_sytem in self.env['res.dating.matching'].sudo().search([]):
             
            method = '_dating_match_action_%s' % (match_sytem.match_name,)
 	    action = getattr(self, method, None)
 	        
 	    if not action:
                raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
 	
 	    #Call the submit action, passing the action settings and the history object
            search_list = action(search_list)

            
        my_dates = self.env['res.partner'].sudo().search(search_list)
            
        return my_dates
            
    @api.model
    def dating_suggestion_email(self):
        """Send email to people surggesting possible partners"""
        
        #send an email out to everyone in the category
        notification_template = self.env['ir.model.data'].sudo().get_object('website_dating', 'dating_suggestions_email')
        profile_template = self.env['ir.model.data'].sudo().get_object('website_dating', 'dating_suggestions_profile_email')

        for rec in self.env['res.partner'].search([('setting_email_suggestion','=', True), ('fake_profile', '=', False), ('dating', '=', True)]):
        
            my_dates = rec.get_dating_suggestions()

            dating_suggestions_html = ""

            for i in range(0, 3):
                rand_date = randint(1, len(my_dates) -1 )
                my_date =  my_dates[rand_date]

                profile_values = profile_template.generate_email(my_date.id)
                dating_suggestions_html += profile_values['body_html']

            values = notification_template.generate_email(rec.id)
            values['body_html'] = values['body_html'].replace("_dating_suggestions_", dating_suggestions_html)
            send_mail = self.env['mail.mail'].create(values)
            #send_mail.send(True)
   
class ResPartnerWebsiteDatingGender(models.Model):

    _name = "res.partner.gender"
    _description = "Partner Gender"
    
    name = fields.Char(string="Gender")
    letter = fields.Char(string="Letter")