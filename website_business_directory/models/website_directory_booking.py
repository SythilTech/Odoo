# -*- coding: utf-8 -*-
from openerp import api, fields, models

class WebsiteDirectoryBooking(models.Model):

    _name = "website.directory.booking"

    partner_id = fields.Many2one('res.partner', string="Business")
    booking_name = fields.Char(string="Booking Name")
    email = fields.Char(string="Email")
    number_of_people = fields.Char(string="Number of People")
    booking_datetime = fields.Datetime(string="Booking Date Time")
    notes = fields.Text(string="Notes")