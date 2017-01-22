# -*- coding: utf-8 -*-
from datetime import datetime, date
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
    def dating_suggestion_email(self):
        """Send email to people surggesting possible partners"""
        
        #send an email out to everyone in the category
        notification_template = self.env['ir.model.data'].sudo().get_object('website_dating', 'dating_suggestions_email')

        for rec in self.env['res.partner'].search([('setting_email_suggestion','=', True), ('fake_profile', '=', False), ('dating', '=', True)]):
            _logger.error(rec.name)       
            search_list = []
        
            #only dating members
            search_list.append(('dating','=','True'))

            #exclude yourself from the list
            search_list.append(('id','!=', rec.id))

            #opposite gender only
	    male_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
            female_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
            if rec.gender_id.id == male_gender.id:
                search_list.append(('gender_id','=', female_gender.id))
            elif rec.gender_id.id == female_gender.id:
                search_list.append(('gender_id','=', male_gender.id))

            #min age preference
            min_age = rec.age - 5
            search_list.append(('age','>=', min_age))
            
            #max age preference
            max_age = rec.age + 5
            search_list.append(('age','<=', max_age))
            
            #Within 20km
            distance = 20
	    mylon = float(rec.city_id.longitude)
	    mylat = float(rec.city_id.latitude)
	    dist = float(distance) * 0.621371
	    lon_min = mylon-dist/abs(math.cos(math.radians(mylat))*69);
	    lon_max = mylon+dist/abs(math.cos(math.radians(mylat))*69);
	    lat_min = mylat-(dist/69);
	    lat_max = mylat+(dist/69);
            search_list.append(('city_id.longitude','>=',lon_min))
            search_list.append(('city_id.longitude','<=',lon_max))
            search_list.append(('city_id.latitude','<=',lat_min))
            search_list.append(('city_id.latitude','>=',lat_max))
            
            my_dates = self.env['res.partner'].sudo().search(search_list)

            dating_suggestions_html = ""

            for i in range(0, 3):
                rand_date = randint(1, len(my_dates) -1 )
                my_date =  my_dates[rand_date]           

                dating_suggestions_html += my_date.first_name.encode("UTF-8") + " (" + str(my_date.age) + " " + my_date.gender_id.letter.encode("UTF-8") + ")<br/>\n"
                dating_suggestions_html += my_date.profile_micro.encode("UTF-8") + "<br/>\n"
                dating_suggestions_html += my_date.city_id.name.encode("UTF-8") + ", " + my_date.state_id.name.encode("UTF-8") + ", " + my_date.country_id.name.encode("UTF-8") + "<br/>\n"
                dating_suggestions_html += "<img src=\"data:image/jpeg;base64," + str(my_date.image_medium) + "\"/>\n"
                dating_suggestions_html += "<hr/>\n"

            values = notification_template.generate_email(rec.id)
            values['body_html'] = values['body_html'].replace("_dating_suggestions_", dating_suggestions_html)
            send_mail = self.env['mail.mail'].create(values)
            #send_mail.send(True)
   
class ResPartnerWebsiteDatingGender(models.Model):

    _name = "res.partner.gender"
    _description = "Partner Gender"
    
    name = fields.Char(string="Gender")
    letter = fields.Char(string="Letter")