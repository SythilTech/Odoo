# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class VoipCall(models.Model):

    _name = "voip.call"

    partner_id = fields.Many2one('res.partner', string="To")
    status = fields.Selection([('missed','Missed'), ('pending','Pending'), ('active','Active'), ('over','Over')], string='Status', default="precall", help="Pending = Calling person\nActive = currently talking")
    end_time = fields.Datetime(string="End Time", help="Time the call end(semiaccurate)")
    duration = fields.Char(string="Duration", help="Length of the call")
    transcription = fields.Text(string="Transcription", help="Automatic transcription of the call")
    notes = fields.Text(string="Notes", help="Additional comments outside the transcription")