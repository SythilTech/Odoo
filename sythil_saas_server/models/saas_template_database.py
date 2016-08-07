# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from contextlib import closing
import os
import shutil

import openerp
from openerp import api, fields, models

class SaasTemplateDatabase(models.Model):

    _name = "saas.template.database"
    _description = "Preconfigured databases that the website user can select from"""
    
    name = fields.Char(string="Display Name", help="Displayed on the website")
    database_name = fields.Char(string="Database Name", help="The name of the template database in psql")
    image = fields.Binary(string="Image")
    description = fields.Char(string="Description", default="Placeholder description")