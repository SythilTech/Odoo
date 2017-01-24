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
            
    def create_fake_profiles(self):
        self.env['res.partner'].create_fake_dating_profiles(self.country_id, self.state_id, self.num_profiles, self.min_age, self.max_age)