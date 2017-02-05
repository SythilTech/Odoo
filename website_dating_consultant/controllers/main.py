# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)
import hashlib
import openerp.http as http
from openerp.http import request
from odoo.addons.website.models.website import slug
from dateutil.parser import parse
import pytz
from datetime import datetime, timedelta

class WebsiteDatingConsultantController(http.Controller):

    @http.route('/dating/consultants', type="http", auth="public", website=True)
    def dating_consultants(self, **kwargs):
        consultant_department = request.env['ir.model.data'].sudo().get_object('website_dating_consultant', 'consultant_department')
        consultants = request.env['hr.employee'].sudo().search([('department_id', '=', consultant_department.id )])
        return http.request.render('website_dating_consultant.dating_consultants', {'consultants': consultants} )
        
    @http.route('/dating/consultant/<model("hr.employee"):consultant>', type="http", auth="public", website=True)
    def dating_consultant_booking(self, consultant, **kwargs):

        #Public users get redirected to register form since the booking form is designed map bookings back to members profiles
        if request.env.user == request.website.user_id:
            return werkzeug.utils.redirect("/dating/register")

        consultant_department = request.env['ir.model.data'].sudo().get_object('website_dating_consultant', 'consultant_department')
        
        #Display the booking page if they are a consultant
        if consultant.department_id.id == consultant_department.id:
            return http.request.render('website_dating_consultant.dating_consultant_booking', {'consultant': consultant, 'booking_duration': '15'} )
        else:
            return "This is not a dating consultant"

    @http.route('/dating/booking/create', type="http", auth="user", website=True)
    def dating_consultant_booking_create(self, **kw):
        """Creates a booking using the fields on the booking field"""

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value

        consultant = request.env['hr.employee'].sudo().browse( int(values['consultant_id']) )
        
        #worlds worse way of converting to UTC...
        parse_string = values['start']        
        if "+" in parse_string:
            start_date = parse(parse_string.replace("+","-") ).astimezone(pytz.utc)
        elif "-" in parse_string:
            start_date = parse(parse_string.replace("-","+") ).astimezone(pytz.utc)
        
        booking_slot_duration = 15
        stop_time = start_date + timedelta(minutes=booking_slot_duration)
        stop_time = stop_time.strftime("%Y-%m-%d %H:%M:%S")
        start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        _logger.error(start_date)
        _logger.error(stop_time)
        cal_event = request.env['calendar.event'].sudo().create({'user_id': consultant.user_id.id,'name': request.env.user.name + " (Booking)", 'start': start_date, 'stop': stop_time, 'description': values['phone'] + "\n" + values['comment'] })
        
        #Add the member as attendees
        cal_event.partner_ids = [(4, request.env.user.partner_id.id)]

        return werkzeug.utils.redirect("/")

    @http.route('/dating/booking/timeframe/<consultant>', type="http", auth="public", website=True)
    def dating_consultant_booking_timeframe(self, consultant, **kw):
        """Return the avaible time slots"""
        
        consultant = request.env['hr.employee'].sudo().browse(int(consultant))
        return_string = ""
        for time_frame in consultant.calendar_id.attendance_ids:
            return_string += '{'
            
            day_number = 0

            if time_frame.dayofweek == "0":
                day_number = 1

            if time_frame.dayofweek == "1":
                day_number = 2

            if time_frame.dayofweek == "2":
                day_number = 3
                
            if time_frame.dayofweek == "3":
                day_number = 4

            if time_frame.dayofweek == "4":
                day_number = 5

            if time_frame.dayofweek == "5":
                day_number = 6

            if time_frame.dayofweek == "6":
                day_number = 0

            return_string += '"id": "' + str(time_frame.id) + '",'            
            return_string += '"start": "' + str(time_frame.date_from) + " " + str(time_frame.hour_from).replace(".",":") + '",'
            return_string += '"end": "' + str(time_frame.date_to) + " " + str(time_frame.hour_to).replace(".",":") + '",'
            return_string += '"dow": [' + str(day_number) + ']'
            return_string += '},'
                
                
        return_string = return_string[:-1]        
        return "[" +  return_string + "]"
        
    @http.route('/dating/booking/events/<consultant>', type="http", auth="public", website=True)
    def dating_consultant_booking_events(self, consultant, **kw):
        """Get events from calendar.event"""

        consultant = request.env['hr.employee'].sudo().browse(int(consultant))
       
        return_string = ""
        for event in request.env['calendar.event'].sudo().search([('user_id','=', int(consultant.user_id.id) )]):
            return_string += '{'
            return_string += '"id": "' + str(event.id) + '",'
            return_string += '"start": "' + str(event.start_datetime) + '+00:00",'
            return_string += '"end": "' + str(event.stop) + '+00:00"'
            return_string += '},'                
                
        return_string = return_string[:-1]
        return "[" +  return_string + "]"
        