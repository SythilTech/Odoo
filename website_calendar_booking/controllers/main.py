# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
import logging
_logger = logging.getLogger(__name__)
from dateutil.parser import parse
import dateutil
import pytz
from datetime import datetime, timedelta

import openerp.http as http
from openerp.http import request

from openerp.addons.website.models.website import slug

class WebsiteBookingController(http.Controller):

    @http.route('/book/calendar/create', type="http", auth="public", website=True)
    def book_calendar_create(self, **kw):
        """Creates a booking using the fields on the booking field"""

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        calendar = request.env['website.calendar'].sudo().browse( int(values['calendar_id']) )        
        
        #worlds worse way of converting to UTC...
        parse_string = values['start']
        if "+" in parse_string:
            start_date = parse(parse_string.replace("+","-") ).astimezone(pytz.utc)
        elif "-" in parse_string:
            start_date = parse(parse_string.replace("-","+") ).astimezone(pytz.utc)
        
        
        alpha_minutes = calendar.booking_slot_duration * 60        
        stop_time = start_date + timedelta(minutes=alpha_minutes)
        stop_time = stop_time.strftime("%Y-%m-%d %H:%M:%S")
        start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        
        calendar.booking_slot_duration
        cal_event = request.env['calendar.event'].sudo().create({'user_id': calendar.user_id.id,'name': values['name'] + " (Booking)", 'start_datetime': start_date, 'stop_datetime': stop_time, 'booking_email': values['email'], 'description': values['email'] + "\n" + values['comment'] })

        return werkzeug.utils.redirect("/book/calendar/" + str(calendar.id) )

    @http.route('/book/calendar/<calendar>', type="http", auth="public", website=True)
    def book_calendar(self, calendar, **kw):
        """Let's user see all aviable booking times and create bookings"""
        my_calendar = request.env['website.calendar'].sudo().browse( int(calendar) )
        return http.request.render('website_calendar_booking.website_calendar_booking_page', {'calendar': my_calendar})

    @http.route('/book/calendar/timeframe/<calendar>', type="http", auth="public", website=True)
    def book_calendar_timeframe(self, calendar, **kw):
        
        my_calendar = request.env['website.calendar'].sudo().browse(int(calendar))
        return_string = ""
        for time_frame in my_calendar.time_frame_ids:
            return_string += '{'
            
            day_number = 0
            if time_frame.day == "sunday":
                day_number = 0

            if time_frame.day == "monday":
                day_number = 1

            if time_frame.day == "tuesday":
                day_number = 2

            if time_frame.day == "wednesday":
                day_number = 3
                
            if time_frame.day == "thursday":
                day_number = 4

            if time_frame.day == "friday":
                day_number = 5

            if time_frame.day == "saturday":
                day_number = 6
            
            return_string += '"start": "' + str(time_frame.start_time).replace(".",":") + '",'
            return_string += '"end": "' + str(time_frame.end_time).replace(".",":") + '",'
            #return_string += '"className": "booking_calendar_book_time",'
            return_string += '"dow": [' + str(day_number) + ']'
            return_string += '},'
                
                
        return_string = return_string[:-1]        
        return "[" +  return_string + "]"
        
    @http.route('/book/calendar/events/<user>', type="http", auth="public", website=True)
    def book_calendar_events(self, user, **kw):
        """Get events from calendar.event"""
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
                    
        return_string = ""
        #for event in request.env['calendar.event'].sudo().search([('user_id','=', int(user) ), ('start_datetime','>=',values['start']), ('start_datetime','<=', values['end'] ) ]):
        for event in request.env['calendar.event'].sudo().search([('user_id','=', int(user) )]):
            return_string += '{'
            return_string += '"title": "' + event.name + '",'
            return_string += '"id": "' + str(event.id) + '",'
            return_string += '"start": "' + str(event.start_datetime) + '+00:00",'
            return_string += '"end": "' + str(event.stop) + '+00:00"'
            return_string += '},'                
                
        return_string = return_string[:-1]
        return "[" +  return_string + "]"
        