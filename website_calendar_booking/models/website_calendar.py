# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class WebsiteCalendar(models.Model):

    _name = "website.calendar"
    
    name = fields.Char(string="Name", required=True)
    user_id = fields.Many2one('res.users',string="User", required=True, help="The user the bookings are for")
    booking_slot_duration = fields.Float(string="Booking Slot Duration", default="0.5")
    booking_min_time = fields.Char(string="Min Booking Time", help="Time before this is cut off the calendar to reduce it's size", compute="_booking_min_time")
    booking_max_time = fields.Char(string="Min Booking Time", help="Time after this is cut off the calendar to reduce it's size",  compute="_booking_max_time")
    url = fields.Char(string="URL", compute="_compute_url")
    time_frame_ids = fields.One2many('website.calendar.timeframe', 'calendar_id', required=True, string="Time Frames", help="Time frames that bookings are allowed for this user, can be multiple per day and different on each day")
        
    def _compute_url(self):
        self.url = request.httprequest.host_url + "book/calendar/" + str(self.id)

    @api.depends('time_frame_ids')
    def _booking_min_time(self):
        #The timeframe with the lowest start time is the time the calendar starts
        min_time = 25.0
        for time_frame in self.time_frame_ids:
            if time_frame.start_time < min_time:
                min_time = time_frame.start_time
        
        self.booking_min_time = str(min_time).replace(".",":")

    @api.depends('time_frame_ids')
    def _booking_max_time(self):
        #The timeframe with the highest end time is the time the calendar ends
        max_time = 0.0
        for time_frame in self.time_frame_ids:
            if time_frame.end_time > max_time:
                max_time = time_frame.end_time
        
        self.booking_max_time = str(max_time).replace(".",":")
    
class WebsiteCalendarTimeframe(models.Model):

    _name = "website.calendar.timeframe"
    
    calendar_id = fields.Many2one('website.calendar', string="Calendar")
    day = fields.Selection([('monday','Monday'), ('tuesday','Tuesday'), ('wednesday','Wednesday'), ('thursday','Thursday'), ('friday','Friday'), ('saturday','Saturday'), ('sunday','Sunday')], string="Day")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")