# -*- coding: utf-8 -*-
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResPartnerInterest(models.Model):

    _name = "res.partner.interest"
    _description = "Partner Interest"

    name = fields.Char(string="Name")
    interest_category_id = fields.Many2one('res.partner.interest.category', string="Interest Category")
    num_interested = fields.Integer(string="Number with Interest", compute="_compute_num_interested")

    @api.one
    def _compute_num_interested(self):
        self.num_interested = self.env['res.partner'].search_count([('interest_list','=',self.id)])
    
class ResPartnerInterestCategory(models.Model):

    _name = "res.partner.interest.category"
    _description = "Partner Interest Category"

    name = fields.Char(string="Name")
    interest_list = fields.One2many('res.partner.interest', 'interest_category_id', string="Interest List")

class ResPartnerInterestFake(models.Model):

    _name = "res.partner.interest.fake"
    _description = "Partner Interest Fake"

    fake = fields.Char(string="Fake")
    
    @api.one
    def create_fake_interests(self):
        for fake_profile in self.env['res.partner'].search([('dating','=',True)]):
            #Go through each interest
            for interest in self.env['res.partner.interest'].search([]):
                #50 / 50 chance of having this interest
                if randint(0,1):
                    fake_profile.interest_list = [(4, interest.id)]