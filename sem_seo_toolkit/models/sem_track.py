# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemTrack(models.Model):

    _name = "sem.track"

    session_id = fields.Char(string="Session ID")
    referrer = fields.Char(string="Referrer")
    user_agent = fields.Char(string="User Agent")
    start_url = fields.Char(string="URL")
    ip = fields.Char(string="IP Address")