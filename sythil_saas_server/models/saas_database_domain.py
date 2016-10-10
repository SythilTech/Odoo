# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class SaasDatabaseDomain(models.Model):

    _name = "saas.database.domain"
    
    database_id = fields.Many2one('saas.database', string="Database")
    name = fields.Char(string="Domain Name")