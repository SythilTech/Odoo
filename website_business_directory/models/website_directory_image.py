# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class WebsiteDirectoryImage(models.Model):

    _name = "website.directory.image"
    
    listing_id = fields.Many2one('res.partner', string="Listing")
    data = fields.Binary(string="Image")
    description = fields.Char(string="Description")