# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class VoipRoom(models.Model):

    _name = "voip.room"
    _description = "Obsolete"

    partner_ids = fields.Many2many('res.partner', string="Participants")
