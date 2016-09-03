from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime
import math
from lxml import etree
import unicodedata
import re
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web

class TakeawayRestaurant(models.Model):

    _name = "takeaway.restaurant"
    
    name = fields.Char(string='Restaurant Name')
    image = fields.Binary(string="Image")
    location_id = fields.Many2one('res.better.zip',string="Location")
    street = fields.Char(string="Street Address")
    latitude = fields.Float(string="Latitude", readonly=True)
    longitude = fields.Float(string="Longitude", readonly=True)
    delivary_radius_kilometers = fields.Float(string="Delivary Radius(Kilometers)")
    delivary_suburbs = fields.Many2many('res.better.zip', string="Delivary Suburbs")
    takeaway_time_monday_start = fields.Float(string="Monday Open Time")
    takeaway_time_monday_end = fields.Float(string="Monday Close Time")
    takeaway_time_tuesday_start = fields.Float(string="Tuesday Open Time")
    takeaway_time_tuesday_end = fields.Float(string="Tuesday Close Time")
    takeaway_time_wednesday_start = fields.Float(string="Wednesday Open Time")
    takeaway_time_wednesday_end = fields.Float(string="Wednesday Close Time")
    takeaway_time_thursday_start = fields.Float(string="Thursday Open Time")
    takeaway_time_thursday_end = fields.Float(string="Thursday Close Time")
    takeaway_time_friday_start = fields.Float(string="Friday Open Time")
    takeaway_time_friday_end = fields.Float(string="Friday Close Time")
    takeaway_time_saturday_start = fields.Float(string="Saturday Open Time")
    takeaway_time_saturday_end = fields.Float(string="Saturday Close Time")
    takeaway_time_sunday_start = fields.Float(string="Sunday Open Time")
    takeaway_time_sunday_end = fields.Float(string="Sunday Close Time")
    cuisines = fields.Many2many('takeaway.cuisine', string="Cuisines")
    cuisine_string = fields.Char(compute="cuisine_st", store="True", string="Cuisine String")
    min_order = fields.Float(String="Min Order")
    slug = fields.Char(string="Slug")
    pos_cats = fields.Many2many('pos.category', string="Categories")
    
    @api.depends('cuisines')
    def cuisine_st(self):
        temp_string = ""
        for cusi in self.cuisines:
            temp_string += cusi.name + ", "
        temp_string = temp_string[:-2]
        self.cuisine_string = temp_string
    
    @api.model
    def create(self, values):
        new_rec = super(TakeawayRestaurant, self).create(values)
        
        if new_rec.location_id:
        
            location_string = ""
            
            if new_rec.street != False:
                location_string += new_rec.street
            
            if new_rec.location_id.city != False:
                location_string += ", " + new_rec.location_id.city
            
            if new_rec.location_id.state_id.name != False:
                location_string += ", " + new_rec.location_id.state_id.name
            
            if new_rec.location_id.country_id.name != False:
                location_string += ", " + new_rec.location_id.country_id.name
            
            try:
                response_string = requests.post("http://nominatim.openstreetmap.org/search/" + location_string + "?format=xml")
                root = etree.fromstring(str(response_string.text.encode('utf-8')))
                my_elements = root.xpath('//place')
                
                new_rec.longitude = str(my_elements[0].attrib['lon'])
                new_rec.latitude = str(my_elements[0].attrib['lat'])
            except:
                _logger.error("Failed to geocode")
            
            mylon = float(new_rec.longitude)
            mylat = float(new_rec.latitude)
            dist = new_rec.delivary_radius_kilometers * 0.621371
            lon_min = mylon-dist/abs(math.cos(math.radians(mylat))*69);
            lon_max = mylon+dist/abs(math.cos(math.radians(mylat))*69);
            lat_min = mylat-(dist/69);
            lat_max = mylat+(dist/69);
            
            
            
            del_suburbs = self.env['res.better.zip'].search([('longitude','>=',lon_min), ('longitude','<=',lon_max), ('latitude','<=',lat_min), ('latitude','>=',lat_max)])
            
            for subby in del_suburbs:
                new_rec.delivary_suburbs = [(4, subby.id)]
            
        return new_rec

    @api.one
    @api.onchange('name')
    def _restaurant_slug(self):
        self.slug = slugify(self.name)

def slugify(s, max_length=None):
    """ Transform a string to a slug that can be used in a url path.

    This method will first try to do the job with python-slugify if present.
    Otherwise it will process string by stripping leading and ending spaces,
    converting unicode chars to ascii, lowering all chars and replacing spaces
    and underscore with hyphen "-".

    :param s: str
    :param max_length: int
    :rtype: str
    """
    s = ustr(s)
    uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub('[\W_]', ' ', uni).strip().lower()
    slug = re.sub('[-\s]+', '-', slug)

    return slug[:max_length]