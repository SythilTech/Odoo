# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemSearchDevice(models.Model):

    _name = "sem.search.device"

    name = fields.Char(string="Name")
    user_agent = fields.Char(string="User Agent")