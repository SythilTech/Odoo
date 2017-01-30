# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from random import randint
from odoo.addons.website.models.website import slug
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)

import openerp.http as http
from openerp.http import request

class WebsiteDatingEventsController(http.Controller):


    @http.route('/dating/events/feedback/<reg>', type="http", auth="user", website=True)
    def dating_events_feedback(self, reg, **kwargs):
        """Get feedback on the event including who you liked"""
        reg = request.env['event.registration'].sudo().browse( int(reg) )
        
        #They have to be signed in as the registrant for this to work
        if request.env.user.partner_id.id == reg.partner_id.id:
            #They can only provide feedback for an event once
            if request.env['res.dating.event.feedback'].sudo().search_count([('partner_id','=', request.env.user.partner_id.id), ('event_id','=', reg.event_id.id)]) == 0:
                
                #Get everyone that went to the event excluding yourself
                singles = request.env['event.registration'].sudo().search([('event_id', '=', reg.event_id.id), ('id','!=', reg.id)])
                return http.request.render('website_dating_events.dating_events_feedback', {'reg': reg, 'singles': singles} )
            else:
                return "You already gave feedback on this event"
        else:
            return "Invalid feedback link"

    @http.route('/dating/events/feedback/<reg>/process', type="http", auth="user", website=True)
    def dating_events_feedback_process(self, reg, **kwargs):
        """Create the feedback record if they haven't already submitted thier feedback"""
                
	values = {}
        for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
        reg = request.env['event.registration'].sudo().browse( int(reg) )
        
        #They have to be signed in as the registrant for this to work
        if request.env.user.partner_id.id == reg.partner_id.id:
            #They can only provide feedback for an event once
            if request.env['res.dating.event.feedback'].sudo().search_count([('partner_id','=', request.env.user.partner_id.id), ('event_id','=', reg.event_id.id)]) == 0:
                
                event_feedback_rating = values['event_feedback_rating']
                
                if event_feedback_rating < 0:
                    event_feedback_rating = 0
                
                if event_feedback_rating > 5:
                    event_feedback_rating = 5
                
                venue_feedback_rating = values['venue_feedback_rating']
                
                if venue_feedback_rating < 0:
                    venue_feedback_rating = 0
                    
                if venue_feedback_rating > 5:
                    venue_feedback_rating = 5
                    
                request.env['res.dating.event.feedback'].sudo().create({'reg_id': reg.id, 'partner_id': reg.partner_id.id, 'event_id': reg.event_id.id, 'event_feedback': values['event_feedback'], 'event_feedback_rating': event_feedback_rating, 'venue_feedback': values['venue_feedback'], 'venue_feedback_rating': venue_feedback_rating, 'venue_id': reg.event_id.address_id.id})                
            
                #Register the likes / dislikes
                for single in request.env['event.registration'].sudo().search([('event_id', '=', reg.event_id.id), ('id','!=', reg.id)]):
                    affinity = values['single_' + str(single.id) ]
                    if affinity == "Like":

                        #Create the like
                        request.env['res.partner.dating.like'].sudo().create({'event_id': reg.event_id.id, 'partner_id': request.env.user.partner_id.id, 'like_partner_id': single.partner_id.id})
  
                        #Create a notification about the like
                        request.env['res.partner.dating.notification'].sudo().create({'has_read': False, 'partner_id': single.partner_id.id, 'content': request.env.user.partner_id.first_name.encode("UTF-8") + " likes you", 'ref_url': '/dating/profile/' + str(single.partner_id.id) })

                    elif affinity == "Dislike":
                        #Create Block
                        request.env['res.partner.dating.block'].sudo().create({'partner_id': request.env.user.partner_id.id, 'block_partner_id': single.partner_id.id})
                    
                return werkzeug.utils.redirect("/")
            else:
                return "You already gave feedback on this event"
        else:
            return "Invalid feedback link"        

    @http.route('/dating/events/local', type="http", auth="user", website=True)
    def dating_events_local(self, **kwargs):
        """Redirect to events in thier local state"""
        return werkzeug.utils.redirect("/dating/events/" + slug(request.env.user.partner_id.state_id) )
        
    @http.route('/dating/events/<model("res.country.state"):state>', type="http", auth="public", website=True)
    def dating_events_local_state(self, state, **kwargs):
        """Events in there state"""
        dating_events = request.env['event.event'].search([('dating','=',True), ('state','=','confirm')])
        
        return http.request.render('website_dating_events.dating_events', {'dating_events': dating_events, 'state_name': state.name} )

        
    @http.route('/dating/events/register/<model("event.event"):event>', type="http", auth="user", website=True)
    def dating_events_register(self, event, **kwargs):
        """Register the user into the event"""

        if request.env.user.partner_id.age < event.min_age:
            return "Not older enough"
            
        if request.env.user.partner_id.age > event.max_age:
            return "Too old"

        male_gender = request.env['ir.model.data'].get_object('website_dating', 'website_dating_male')
        female_gender = request.env['ir.model.data'].get_object('website_dating', 'website_dating_female')

        #Check if there is slots for thier gender
        if request.env.user.partner_id.gender_id.id == male_gender.id:
            if event.current_males >= event.max_males:
                return "Max males already reached"        
        elif request.env.user.partner_id.gender_id.id == female_gender.id:
            if event.current_females >= event.max_females:
                return "Max females already reached"
        
        request.env['event.registration'].sudo().create({'event_id': event.id, 'partner_id': request.env.user.partner_id.id})
        return werkzeug.utils.redirect("/")