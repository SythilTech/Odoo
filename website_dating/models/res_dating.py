# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResDating(models.Model):

    _name = "res.dating"
    _description = "Dating"
    
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string="State")
    num_profiles = fields.Integer(string="Num Profiles", default="1000")
    min_age = fields.Integer(string="Min Age", default="18")
    max_age = fields.Integer(string="Max Age", default="60")

    @api.one
    def delete_fake_profiles(self):
        """Delete all fake dating profiles"""
        for fake in self.env['res.partner'].search([('fake_profile','=',True)]):
            fake.unlink()
    
    @api.one
    def create_fake_profiles(self):
        """Create a large amount of fake profile to aid in testing of dating algorithm"""
                
        calc_min_days = 365 * self.min_age
        calc_max_days = 365 * self.max_age
                
        my_delta_young_time = datetime.utcnow() - timedelta(days=calc_min_days)
        my_delta_old_time = datetime.utcnow() - timedelta(days=calc_max_days)	        

        suburb_list = self.state_id.city_ids

        male_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        female_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
        
        for i in range(0, self.num_profiles):
	    #random name and with it gender
            first_name = self.env['res.dating.fake.first'].browse( randint(1, 4999) )
            last_name = self.env['res.dating.fake.last'].browse( randint(1, 4999) )
            
            #random age
	    birth_date = my_delta_old_time + timedelta(seconds=randint(0, int((my_delta_young_time - my_delta_old_time).total_seconds())))
            age = relativedelta(date.today(), birth_date).years
            
            #random suburb
            rand_suburb = suburb_list[randint(0, len(suburb_list) - 1)]
            
            #random profile text
            profile_text = "I am " + str(age) + " year old " + first_name.gender_id.name.lower() + " looking for a relationship."
            
            #create the partner
            new_partner = self.env['res.partner'].create({'profile_micro': profile_text,'dating':'True', 'fake_profile':'True', 'birth_date': birth_date, 'name': first_name.name + " " + last_name.name, 'first_name':first_name.name, 'last_name':last_name.name,'gender_id': first_name.gender_id.id, 'country_id':rand_suburb.state_id.country_id.id, 'state_id':rand_suburb.state_id.id, 'city':rand_suburb.name, 'city_id':rand_suburb.id, 'age':age})