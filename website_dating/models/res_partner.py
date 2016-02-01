# -*- coding: utf-8 -*-
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models

class ResPartnerWebsiteDating(models.Model):

    _inherit = "res.partner"

    dating = fields.Boolean(string="Dating")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    fake_profile = fields.Boolean(string="Fake Profile")
    birth_date = fields.Date(string="DOB")
    age = fields.Integer(string="Age")
    gender = fields.Many2one('res.partner.gender', string="Gender")
    gender_pref = fields.Many2many('res.partner.gender', string="Gender Preference")
    min_age_pref = fields.Integer(string="Min Age Preference")
    max_age_pref = fields.Integer(string="Max Age Preference")
    dist_pref = fields.Integer(string="Distance Pref")
    relationship_type = fields.Many2one('res.partner.relationship', string="Relationship Type", help="The type of relationship this member is seeking")
    interest_list = fields.Many2many('res.partner.interests', string="Interest List")
    profile_visibility = fields.Selection([('public','Public'), ('members_only','Members Only'), ('not_listed','Not Listed')], default="not_listed", string="Profile Visibility", help="Public: can be viewed by anyone on the internet\nMembers Only: Can only be viewed by people who have an account\nNot Listed: Profile will only be visiable to members you have contacted")
    profile_text = fields.Text(string="Profile Text")
    profile_micro = fields.Char(size=100, string="Profile Micro Summary")
    like_list = fields.Many2many(comodel_name='res.partner', relation='like_list', column1='like1', column2='like2', string='Like List')
    message_setting = fields.Selection([('public','Anyone'), ('members_only','Members Only'), ('i_like','Members I Like')], string="Message Setting")
    contacts = fields.One2many('res.dating.contacts', 'partner_id', string="Contact List", help="A member that has contacted you or you have contacted them")
        
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
                
class ResPartnerWebsiteDatingGender(models.Model):

    _name = "res.partner.gender"

    name = fields.Char(string="Gender")
    letter = fields.Char(string="Letter")
    
class ResPartnerInterests(models.Model):

    _name = "res.partner.interests"

    name = fields.Char(string="Name")
    interest_category_id = fields.Many2one('res.partner.interest.categories', string="Interest Category")
    
class ResPartnerInterestCategories(models.Model):

    _name = "res.partner.interest.categories"

    name = fields.Char(string="Name")
    interest_list = fields.One2many('res.partner.interests', 'interest_category_id', string="Interest List")
    
class ResPartnerRelationship(models.Model):

    _name = "res.partner.relationship"

    name = fields.Char(string="Name")
