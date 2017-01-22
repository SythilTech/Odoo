# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResCountryStateDating(models.Model):

    _inherit = "res.country.state"
    
    city_ids = fields.One2many('res.country.state.city', 'state_id', string="Cities")