from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)

import werkzeug
import werkzeug.urls
import random

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.tools.translate import _
import requests
from lxml import etree

class Osmer(models.Model):

    _inherit = "event.event"

    osmer_secret = fields.Char(string="Osmer Secret")
 
    @api.multi
    def open_map(self):
        self.ensure_one()
        rand_number = random.randint(1, 1000000)
        map_url = request.httprequest.host_url + "osmer_map?secret=" + str(rand_number)
        self.write({'osmer_secret':rand_number})
        return {
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
                  'url'      : map_url
               }        

class MyController(http.Controller):

    @http.route('/osmer_map',type="http")
    def some_code(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        my_string = ""
        
        my_event = request.env['event.event'].sudo().search([('osmer_secret','=',values['secret'])],limit=1)[0]
	
	if my_event == False:
	    return "Map does not exist"
	my_event.osmer_secret = ""
        my_event.osmer_url = ""

        lat_average = 0.0
        long_average = 0.0
        end_string = ""
        reg_count = 0
        
        for reg in my_event.registration_ids:
            location_string = ""
            
            if reg.partner_id.street != False:
                location_string += reg.partner_id.street
            
            if reg.partner_id.city != False:
                location_string += ", " + reg.partner_id.city
            
            if reg.partner_id.state_id.name != False:
                location_string += ", " + reg.partner_id.state_id.name
            
            if reg.partner_id.country_id.name != False:
                location_string += ", " + reg.partner_id.country_id.name
            
            
            #location = geolocator.geocode(location_string)     
            response_string = requests.post("http://nominatim.openstreetmap.org/search/" + location_string + "?format=xml")
            
            root = etree.fromstring(str(response_string.text.encode('utf-8')))
            my_elements = root.xpath('//place')
	        
	    if len(my_elements) != 0:
	        my_lat = my_elements[0].attrib['lat']
	        my_long = my_elements[0].attrib['lon']
	
                if reg_count == 0:
                    lat_average = my_lat
                    long_average = my_long
                else:
                    #average the lat/long with the current
                    lat_average = (float(lat_average) + float(my_lat)) / 2
                    long_average = (float(long_average) + float(my_long)) / 2
                    
                end_string += 'var lonLat = new OpenLayers.LonLat(' +  str(my_long) +  ',' + str(my_lat) + ')' + "\n"
                end_string += '          .transform(' + "\n"
		end_string += '            new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984' + "\n"
		end_string += '            map.getProjectionObject() // to Spherical Mercator Projection' + "\n"
		end_string += '          );' + "\n"
 
                
                end_string += 'marker = new OpenLayers.Marker(lonLat);' + "\n"
                end_string += 'markers.addMarker(marker);' + "\n"
                end_string += 'marker.icon.imageDiv.title = "' + reg.name + '";' + "\n"
            reg_count += 1

        my_string += '<html><body>' + "\n"
        my_string += '<div id="mapdiv"></div>' + "\n"
        my_string += '<script src="http://www.openlayers.org/api/OpenLayers.js"></script>' + "\n"
        my_string += '<script>' + "\n"
        my_string += '    map = new OpenLayers.Map("mapdiv");' + "\n"
        my_string += '    map.addLayer(new OpenLayers.Layer.OSM());' + "\n"
 
        my_string += '    var lonLatAverage = new OpenLayers.LonLat(' +  str(long_average) +  ',' + str(lat_average) + ')' + "\n"
        my_string += '          .transform(' + "\n"
        my_string += '            new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984' + "\n"
        my_string += '            map.getProjectionObject() // to Spherical Mercator Projection' + "\n"
        my_string += '          );' + "\n"
 
        my_string += '    var zoom=9;' + "\n"
 
        my_string += '    var markers = new OpenLayers.Layer.Markers( "Markers" );' + "\n"
        my_string += '    map.addLayer(markers);' + "\n"
 
 
        my_string += end_string
 
 
        my_string += '    map.setCenter (lonLatAverage, zoom);' + "\n"
        my_string += '</script>' + "\n"
        my_string += '</body></html>' + "\n"

        return my_string
        
        
