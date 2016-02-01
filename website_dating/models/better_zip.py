# -*- coding: utf-8 -*-
from openerp import api, fields, models

class BetterZipWebsiteDating(models.Model):

    _inherit = "res.better.zip"
    
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    
class BetterZipGeonamesImportWebsiteDating(models.Model):

    _inherit = "better.zip.geonames.import"
    
    @api.model
    def _prepare_better_zip(self, row, country):
        """Override base method to get latitude and longitude co-ordinates from geonames"""
        state = self.select_or_create_state(row, country)
        vals = {
            'name': row[1],
            'city': self.transform_city_name(row[2], country),
            'state_id': state.id,
            'latitude': row[9],
            'longitude': row[10],
            'country_id': country.id,
            }
        return vals
