# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class CalendarEventEmail(models.Model):

    _inherit = "calendar.event"
    
    booking_email = fields.Char(string="Email")