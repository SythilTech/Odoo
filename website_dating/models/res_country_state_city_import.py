# -*- coding: utf-8 -*-
import StringIO
import zipfile
import unicodecsv
import csv
import requests
import logging
_logger = logging.getLogger(__name__)

from openerp.exceptions import Warning
from openerp import api, fields, models

class ResCountryStateCityImport(models.Model):

    _name = "res.country.state.city.import"
    
    country_id = fields.Many2one('res.country', required=True, string='Country')
    
    
    @api.one
    def geonames_import(self):
        geonames_url = "http://download.geonames.org/export/zip/" + self.country_id.code + ".zip"
        
        geonames_request = requests.get(geonames_url)
        if geonames_request.status_code != requests.codes.ok:
            raise Warning("Failed to download file from geonames")
        
        geonames_zip = zipfile.ZipFile(StringIO.StringIO(geonames_request.content))
	
	csv_file = geonames_zip.open(self.country_id.code + ".txt")
        reader = csv.reader(StringIO.StringIO(csv_file.read()), delimiter='	')
        
        for row in reader:
            city_name = row[2]
            state_name = row[3]
            state_code = row[4]
            latitude = row[9]
            longitude = row[10]
            
            #Create the state if it doesn't exist
            state_search = self.env['res.country.state'].search([('name','=',state_name), ('country_id','=', self.country_id.id)])
            if len(state_search) == 0:
                state = self.env['res.country.state'].create({'name': state_name, 'code':state_code, 'country_id': self.country_id.id})
            else:
                state = state_search[0]

            self.env['res.country.state.city'].create({'name': city_name, 'state_id': state.id, 'latitude': latitude, 'longitude': longitude})