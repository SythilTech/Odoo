# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from random import randint
import datetime

from openerp import api, fields, models

class EventEventDating(models.Model):

    _inherit = "event.event"

    dating = fields.Boolean(string="Dating Event")
    current_males = fields.Integer(string="Current Males", compute="_compute_current_males", store=True)
    max_males = fields.Integer(string="Max Males")
    current_females = fields.Integer(string="Current Females", compute="_compute_current_females", store=True)
    max_females = fields.Integer(string="Max Females")
    min_age = fields.Integer(string="Min Age")
    max_age = fields.Integer(string="Max Age")
    dating_description = fields.Text(string="Website Description")
    event_feedback_ids = fields.One2many('res.dating.event.feedback', 'event_id', string="Event Feedback")
    dating_price = fields.Float(String="D Price")
    max_attendee_distance = fields.Integer(default="40075", string="Max Attendee Distance (km)", help="Members can not attend the event if they live too far away")
    dating_filter_ids = fields.Many2many('ir.filters', domain=[('model_id','=','res.partner')], string="Dating Event Filters")

    @api.model
    def dating_events_create(self):
        """Auto creates a dating event"""
        
        dating_list = self.env['res.partner'].sudo().search([('dating','=',True), ('fake_profile','=',False)])

        #The event is based around a random member (age and location), this way locations with more members get more events
        random_member = dating_list[randint(0, len(dating_list) - 1)]
        min_age = random_member.age - 5
        max_age = random_member.age + 5
        _logger.error(random_member.state_id.name)
        dating_locations_in_state = self.env['res.partner'].sudo().search([('dating_event_location','=',True),('state_id','=',random_member.state_id.id)])
        random_location = dating_locations_in_state[randint(0, len(dating_locations_in_state) - 1)]
        random_name = random_location.name.encode("UTF-8") + " for " + str(min_age) + " to " + str(max_age)
        
        date_begin = datetime.datetime.now() + datetime.timedelta(90)
        date_end = datetime.datetime.now() + datetime.timedelta(+91)
        
        self.env['event.event'].sudo().create({'dating': True, 'name': random_name, 'min_age': min_age, 'max_age': max_age, 'max_males': 3, 'max_females': 3, 'dating_description': random_name, 'date_begin':date_begin, 'date_end':date_end, 'date_tz':'Australia/Melbourne'})

    @api.depends('registration_ids')
    def _compute_current_males(self):
        male_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        for event in self:
            male_count = 0
            for reg in event.registration_ids:
                if reg.partner_id.gender_id.id == male_gender.id:
                    male_count += 1
            event.current_males = male_count
    
    @api.depends('registration_ids')
    def _compute_current_females(self):
        female_gender = self.env['ir.model.data'].get_object('website_dating', 'website_dating_female')
        for event in self:
            female_count = 0
            for reg in event.registration_ids:
                 if reg.partner_id.gender_id.id == female_gender.id:
                    female_count += 1
            event.current_females = female_count