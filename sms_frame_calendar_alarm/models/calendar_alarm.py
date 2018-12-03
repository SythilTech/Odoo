# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools

class CalendarAlarm(models.Model):

    _inherit = "calendar.alarm"

    type = fields.Selection( selection_add=[("sms", "SMS")] )