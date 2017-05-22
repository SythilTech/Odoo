# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class WebsiteDirectoryStat(models.Model):

    _name = "website.directory.stat"
    
    listing_id = fields.Many2one('res.partner', string="Listing")
    ref = fields.Char(string="Referer URL")
    ip = fields.Char(string="IP Address")
    location = fields.Char(string="Geo Location")
    
class WebsiteDirectoryStatWebsite(models.Model):

    _name = "website.directory.stat.website"
    
    listing_id = fields.Many2one('res.partner', string="Listing")
    ip = fields.Char(string="IP Address")
    location = fields.Char(string="Geo Location")