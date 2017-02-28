# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class WebsiteDirectoryFieldType(models.Model):

    _name = "website.directory.field.type"
    
    name = fields.Char(string="Name")
    internal_type = fields.Char(string="Internal Type", help="Calls the funtion to generate the HTML")
    
class WebsiteDirectoryField(models.Model):

    _name = "website.directory.field"
    
    field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model','=','res.partner')], string="ORM Field")
    field_type = fields.Many2one('website.directory.field.type', string="Field Type")