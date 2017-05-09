# -*- coding: utf-8 -*-
import pyodbc
import requests
import base64
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

from openerp import api, tools, fields, models
from odoo.exceptions import ValidationError, UserError

class MigrationImportOdbcDsn(models.Model):

    _name = "migration.import.odbc.dsn"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")
    connection_string = fields.Char(string="Connect String")
    storage = fields.Selection([('file','File'),('online','Online')], string="Storage")

class MigrationImportOdbcConnect(models.Model):

    _name = "migration.import.odbc.connect"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")
    connection_string = fields.Char(string="Connect String")
    storage = fields.Selection([('file','File'),('online','Online')], string="Storage")