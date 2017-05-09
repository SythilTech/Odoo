# -*- coding: utf-8 -*-
import pyodbc
import requests
import base64
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

from openerp import api, tools, fields, models
from odoo.exceptions import ValidationError, UserError

class MigrationImportOdbcRelationship(models.Model):

    _name = "migration.import.odbc.relationship"

    import_id = fields.Many2one('migration.import.odbc', string="Import ID")
    table1 = fields.Many2one('migration.import.odbc.table', string="Table")
    table1_id_field = fields.Many2one('migration.import.odbc.table.field', string="Table Field")
    table2 = fields.Many2one('migration.import.odbc.table', string="Other Table")
    table2_id_field = fields.Many2one('migration.import.odbc.table.field', string="Other Table ID Field")
    table2_name_field = fields.Many2one('migration.import.odbc.table.field', string="Other Table Name Field", help="The field in the other database which acts as the name field")
    relationship_type = fields.Selection([('many2one','Many2One')], string="Relationship Type", help="The database relatioship between the 2 fields/tables")