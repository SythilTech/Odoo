# -*- coding: utf-8 -*-
import pyodbc
import requests
import base64
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

from openerp import api, tools, fields, models
from odoo.exceptions import ValidationError, UserError

class MigrationImportOdbcLog(models.Model):

    _name = "migration.import.odbc.log"

    import_id = fields.Many2one('migration.import.odbc', string="Import ID")
    state = fields.Selection([('progress','In Progress'), ('failed','Failed'), ('done','Done')])
    table_ids = fields.One2many('migration.import.odbc.log.table', 'log_id', string="Tables")
    finish_date = fields.Datetime(string="Finish Date")

class MigrationImportOdbcLogTable(models.Model):

    _name = "migration.import.odbc.log.table"

    log_id = fields.Many2one('migration.import.odbc.log', string="Import Log")
    table_id = fields.Many2one('migration.import.odbc.table', string="Import Table")
    imported_records = fields.Integer(string="Imported Records")
    total_records = fields.Integer(string="Total Records")