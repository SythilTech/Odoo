# -*- coding: utf-8 -*-
import pyodbc
import requests
import base64
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

from openerp import api, tools, fields, models
from odoo.exceptions import ValidationError, UserError

class MigrationImportOdbc(models.Model):

    _name = "migration.import.odbc"

    name = fields.Char(string="Name", required="True", translate=True)
    dsn_id = fields.Many2one('migration.import.odbc.dsn', string="Driver")
    connection_string_template = fields.Many2one('migration.import.odbc.connect', string="Connection Template")
    connection_string = fields.Char(string="Connection String", help="See https://www.connectionstrings.com if you want a connection string other then MySQL")
    db_table_ids = fields.One2many('migration.import.odbc.table', 'import_id', string="Database Tables")
    import_log_ids = fields.One2many('migration.import.odbc.log', 'import_id', string="Import Log")
    storage = fields.Selection(string="Storage", related="connection_string_template.storage")
    connect_server = fields.Char(string="Server")
    connect_database = fields.Char(string="Database")
    connect_username = fields.Char(string="Username")
    connect_password = fields.Char(string="Password")
    batch_import_limit = fields.Integer(string="Batch Import Limit", default="100", help="0 = No Limit")

    @api.onchange('name')
    def _onchange_name(self):
        #Check the data sources now so the user doesn't have to click the button
        self.check_data_sources()
    
    @api.multi
    def create_scheduled_import(self):
        self.ensure_one()
        new_cron = self.env['ir.cron'].create({'name': self.name + " Scheduled Import", 'interval_number': 24, 'interval_type': 'hours', 'model': 'migration.import.odbc', 'function': 'run_scheduled_import', 'args': '(' + str(self.id) + ',)'})
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Scheduled Import',
            'view_mode': 'form',
            'res_model': 'ir.cron',
            'res_id': new_cron.id
        }
    
    def run_scheduled_import(self, record_id):
        import_wizard = self.env['migration.import.odbc'].browse(record_id)
        import_wizard.import_all_data()
        
    def import_all_data(self):
        #Run an import on all tables that have a model
        import_log = self.env['migration.import.odbc.log'].create({'import_id': self.id, 'state':'progress'})
        
        for db_table in self.db_table_ids:
            if db_table.model_id:
                db_table.import_table_data(import_log)
        import_log.state = "done"
    
    @api.onchange('connection_string_template','dsn_id','connect_server','connect_database','connect_username','connect_password')
    def _onchange_dsn_id(self):
        if self.dsn_id and self.connection_string_template.connection_string:
            cs = self.connection_string_template.connection_string

            cs = cs.replace("$driver", self.dsn_id.driver)
            
            if self.connect_server:
                cs = cs.replace("$server", self.connect_server)
            
            if self.connect_database:
                cs = cs.replace("$database", self.connect_database)
            
            if self.connect_username:
                cs = cs.replace("$username", self.connect_username)
            
            if self.connect_password:
                cs = cs.replace("$password", self.connect_password)

            self.connection_string = cs
    
    def check_data_sources(self):
	sources = pyodbc.dataSources()
	dsns = sources.keys()
	dsns.sort()
	for dsn in dsns:
	    if self.env['migration.import.odbc.dsn'].search_count([('name','=',dsn)]) == 0:
		self.env['migration.import.odbc.dsn'].create({'name': dsn, 'driver': sources[dsn]})

        #for driver in pyodbc.drivers():
        #    _logger.error(driver)
	
    def test_connection(self):
        conn = pyodbc.connect(self.connection_string)
        conn.close()
        
        #pyodbc will provide most of the error reporting so if you got here I can assume everything went well
        raise UserError("Connection Successful")
    
    def analyse_database(self):
        conn = pyodbc.connect(self.connection_string)
        table_cursor = conn.cursor()
        column_cursor = conn.cursor() #Double cursor because of issue with fetch columns

        for db_table in table_cursor.tables():
            import_table = self.env['migration.import.odbc.table'].search([('import_id','=',self.id), ('name','=',db_table.table_name)])
            if len(import_table) == 0:
                import_table = self.env['migration.import.odbc.table'].create({'import_id': self.id, 'name': db_table.table_name})

            #Get the fields in the table
            for column in column_cursor.columns(table=db_table.table_name):
                column_name = column[3]
                data_type = column[5]
                is_key = column[17]
                
                if is_key == "YES":
                    is_key = True
                elif is_key == "NO":
                    is_key = False
                
                if column_name == "id":
                    is_key = True
                    
                import_field = self.env['migration.import.odbc.table.field'].search([('table_id','=',import_table.id),('name','=',column_name)])
                if len(import_field) == 0:
                    orm_type = False

                    #Try to convert from ? type to ORM field ttype
                    if data_type == "varchar":
                        orm_type = "char"
                    elif data_type == "integer":              
                        orm_type = "integer"
                    
                    self.env['migration.import.odbc.table.field'].create({'table_id': import_table.id, 'name': column_name, 'orm_type': orm_type, 'orm_name': "x_" + column_name, 'is_key': is_key})
    