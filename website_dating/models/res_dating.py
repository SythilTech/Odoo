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
            first_name = self.env['res.dating.fake.first'].browse(randint(1, 4999))
            last_name = self.env['res.dating.fake.last'].browse(randint(1, 4999))
            
            gender = self.env['res.partner.gender'].search([('name','=',first_name.gender)])[0].id

            #random age
	    birth_date = my_delta_old_time + timedelta(seconds=randint(0, int((my_delta_young_time - my_delta_old_time).total_seconds())))
            age = relativedelta(date.today(), birth_date).years

            #random age pref
            min_age_pref = randint(self.min_age, self.max_age)
            max_age_pref = randint(min_age_pref, self.max_age)

            #random relationship type
            relationship_type = self.env['res.partner.relationship'].browse(randint(1, self.env['res.partner.relationship'].search_count([]) ) )
            
            #random suburb
            rand_suburb = suburb_list[randint(0, len(suburb_list) - 1)]
                
            #random profile visibilty
            rand_profile_vis = randint(1, 100)
            profile_vis = ""
            if rand_profile_vis <= 80:
                #80% of being members only
                profile_vis = "members_only"
            elif rand_profile_vis <= 100:
                #20% of being public
                profile_vis = "public"
            
            #random message settings
            rand_message_setting = randint(1, 100)
            message_setting = ""
            if rand_message_setting <= 80:
                #80% of being members only
                message_setting = "members_only"
            elif rand_message_setting <= 100:
                #20% of being public
                message_setting = "public"

            
            #random profile text
            profile_text = "I am " + str(age) + " year old " + first_name.gender + " seeking " + str(relationship_type.name)
            
            #create the partner
            new_partner = self.env['res.partner'].create({'message_setting':message_setting, 'profile_micro': profile_text, 'profile_text': profile_text,'profile_visibility': profile_vis,'dating':'True', 'fake_profile':'True', 'birth_date': birth_date, 'name': first_name.name + " " + last_name.name, 'first_name':first_name.name, 'last_name':last_name.name,'gender':gender, 'country_id':rand_suburb.state_id.country_id.id, 'state_id':rand_suburb.state_id.id, 'city':rand_suburb.name, 'age':age, 'relationship_type': relationship_type.id, 'min_age_pref':min_age_pref,'max_age_pref':max_age_pref, 'latitude': rand_suburb.latitude, 'latitude': rand_suburb.latitude, 'longitude': rand_suburb.longitude})           
            
            #random gender pref
            rand_gender_pref = randint(1, 100)
            if rand_gender_pref <= 80:
                #80% chance of being straight
                if first_name.gender == "Male":
                    new_partner.gender_pref = [(4, female_gender.id)]
                elif first_name.gender == "Female":
                    new_partner.gender_pref = [(4, male_gender.id)]
            elif rand_gender_pref <= 90:
                #10% chance of being gay
                if first_name.gender == "Male":
                    new_partner.gender_pref = [(4, male_gender.id)]
                elif first_name.gender == "Female":
                    new_partner.gender_pref = [(4, female_gender.id)]    
            elif rand_gender_pref <= 100:
                #10% chance of being bi
                new_partner.gender_pref = [(4, male_gender.id)]
                new_partner.gender_pref = [(4, female_gender.id)]
                    

class ResDatingContacts(models.Model):

    _name = "res.dating.contacts"
    
    partner_id = fields.Many2one('res.partner', string='From Partner')
    to_id = fields.Many2one('res.partner', string='To Partner')
    unread_message_count = fields.Integer()
    
class ResDatingMessages(models.Model):

    _name = "res.dating.messages"

    message_owner = fields.Many2one('res.partner', string='Owner')
    message_partner_id = fields.Integer(string='From Partner')
    message_to_id = fields.Integer(string='To Partner')
    message_text = fields.Text(string="Message")
    type =  fields.Selection([('regular','Regular'), ('like','Like')], string="Type")
    read = fields.Boolean(string="Read")