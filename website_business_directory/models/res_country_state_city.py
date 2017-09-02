# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResCountryStateCity(models.Model):

    _name = "res.country.state.city"
    
    name = fields.Char(string='City Name')
    state_id = fields.Many2one('res.country.state', string="State")
    zip = fields.Char(string="Zip")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")