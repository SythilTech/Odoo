# -*- coding: utf-8 -*-
from datetime import datetime
from urllib import urlencode, quote as quote

from openerp import api, fields, models, tools

class CalendarAlarm(models.Model):

    _inherit = "calendar.alarm"
    
    type = fields.Selection( selection_add=[("sms", "SMS")] )