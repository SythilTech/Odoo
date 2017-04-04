# -*- coding: utf-8 -*-
import pyodbc
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from odoo.exceptions import ValidationError, UserError

class MigrationImportOdbc(models.Model):

    _name = "migration.import.odbc"

    name = fields.Char(string="Name", required="True")
    dsn_id = fields.Many2one('migration.import.odbc.dsn', string="ODBC DSN List")
    connection_string_template = fields.Many2one('migration.import.odbc.connect', string="CS Template")
    connection_string = fields.Char(string="Connection String", required="True", help="See https://www.connectionstrings.com if you want a connection string other then MySQL")
    db_table_ids = fields.One2many('migration.import.odbc.table', 'import_id', string="Database Tables")
    import_log_ids = fields.One2many('migration.import.odbc.log', 'import_id', string="Import Log")

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
    
    @api.onchange('connection_string_template')
    def _onchange_connection_string_template(self):
        if self.connection_string_template:
            connection_string = self.connection_string_template.connection_string.replace("$driver",self.dsn_id.driver)
            self.connection_string = connection_string
    
    def check_data_sources(self):
	sources = pyodbc.dataSources()
	dsns = sources.keys()
	dsns.sort()
	for dsn in dsns:
	    if self.env['migration.import.odbc.dsn'].search_count([('name','=',dsn)]) == 0:
		self.env['migration.import.odbc.dsn'].create({'name': dsn, 'driver': sources[dsn]})
	
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

class MigrationImportOdbcDsn(models.Model):

    _name = "migration.import.odbc.dsn"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")

class MigrationImportOdbcConnect(models.Model):

    _name = "migration.import.odbc.connect"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")
    connection_string = fields.Char(string="Connect String")
    
class MigrationImportOdbcLog(models.Model):

    _name = "migration.import.odbc.log"

    import_id = fields.Many2one('migration.import.odbc', string="Import ID")
    state = fields.Selection([('progress','In Progress'), ('failed','Failed'), ('done','Done')])
    table_ids = fields.One2many('migration.import.odbc.log.table', 'log_id', string="Tables")

class MigrationImportOdbcLogTable(models.Model):

    _name = "migration.import.odbc.log.table"

    log_id = fields.Many2one('migration.import.odbc.log', string="Import Log")
    table_id = fields.Many2one('migration.import.odbc.table', string="Import Table")
    imported_records = fields.Integer(string="Imported Records")
    total_records = fields.Integer(string="Total Records")
    
class MigrationImportOdbcTable(models.Model):

    _name = "migration.import.odbc.table"

    import_id = fields.Many2one('migration.import.odbc', string="Import ID")
    name = fields.Char(string="Name", readonly="True")
    model_id = fields.Many2one('ir.model', string="Model", help="The ORM model which the data gets imported into")
    field_count = fields.Integer(string="Fields", compute="_compute_field_count")
    db_field_ids = fields.One2many('migration.import.odbc.table.field', 'table_id', string="Database Fields")
    default_value_ids = fields.One2many('migration.import.odbc.table.default', 'table_id', string="Default Values", help="Set a value before importing into the record into the database")
    select_sql = fields.Char(string="Select SQL", help="Modify this if you want to perform sql transformations such as concat first and last name into name field")

    @api.one
    @api.depends('db_field_ids')
    def _compute_field_count(self):
        self.field_count = len(self.db_field_ids)

    def import_table_data_wrapper(self):
        #Create a import log just for this table
        import_log = self.env['migration.import.odbc.log'].create({'import_id': self.import_id.id, 'state':'progress'})
        self.import_table_data(import_log)
        import_log.state = "done"
        
    def import_table_data(self, import_log):
        conn = pyodbc.connect(self.import_id.connection_string)
        cursor = conn.cursor()
        cursor.execute(self.select_sql)

        import_log_table = self.env['migration.import.odbc.log.table'].create({'log_id':import_log.id, 'table_id': self.id, 'total_records': len(list(cursor)) })

        cursor.execute(self.select_sql) #Issue cursor is lost? after counting total record?!?
        
        defaults = {}
        for default in self.default_value_ids:
            defaults[default.field_id.name] = default.value

        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            
            #Merge the defaults with sql dictionary
            row_dict = dict(zip(columns, row))
            merged_dict = defaults.copy()
            merged_dict.update(row_dict)
            
            if 'id' in merged_dict:
                external_identifier = "import_record_" + self.model_id.model.replace(".","_") + "_" + str(merged_dict['id'])

                #Create a new record if the external ID does not exist
                if self.env['ir.model.data'].xmlid_to_res_id('odbc_import.' + external_identifier) == False:
                    new_rec = self.env[self.model_id.model].create(merged_dict)
                    self.env['ir.model.data'].create({'module': "odbc_import", 'name': external_identifier, 'model': self.model_id.model, 'res_id': new_rec.id })

                #TODO write update record code

                import_log_table.imported_records += 1
            else:
                raise UserError("External ID is neccassary to import")
            
    @api.multi
    def open_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Import DB Table", 
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    @api.onchange('db_field_ids')
    def _onchange_db_field_ids(self):

        sql = ""
        sql += "SELECT "
        for import_field in self.db_field_ids:
            if import_field.field_id:
                if import_field.field_id.name != import_field.name:
                    sql += import_field.name + " as " + import_field.field_id.name + ", "
                else:
                    sql += import_field.name + ", "
            else:
                #Import the primary key but rename it to id so we can create an external id from it
                if import_field.is_key:
                    if import_field.name != 'id':
                        sql += import_field.name + " as id, "
                    else:
                        sql += "id, "
                    
        sql = sql[:-2] + " FROM " + self.name
        self.select_sql = sql
        
    @api.onchange('model_id')
    def _onchange_model_id(self):
        #Try to map the columns to ORM fields
        for column in self.db_field_ids:
            column.model_id = self.model_id.id
            if column.name != "id":
                orm_field = self.env['ir.model.fields'].search([('model_id','=',self.model_id.id), '|', ('name','=',column.name), ('name','=',column.orm_name)])
                if orm_field:
                    column.field_id = orm_field[0].id
            
class MigrationImportOdbcTableField(models.Model):

    _name = "migration.import.odbc.table.field"

    table_id = fields.Many2one('migration.import.odbc.table', string="Database Table")
    name = fields.Char(string="Name", readonly="True")
    orm_type = fields.Char(string="ORM Type")
    model_id = fields.Many2one('ir.model', string="Model ID", related="table_id.model_id")
    orm_name = fields.Char(string="ORM Name")
    field_id = fields.Many2one('ir.model.fields', string="Field", help="The ORM field that the data get imported into")
    is_key = fields.Boolean(string="is Primary Key")
    
    def auto_create_field(self):
        if is_key == False:
            new_field = self.env['ir.model.fields'].create({'ttype': self.orm_type, 'name': self.orm_name, 'field_description':self.name, 'model_id':self.table_id.model_id.id})
            self.field_id = new_field.id
    
class MigrationImportOdbcTableDefault(models.Model):

    _name = "migration.import.odbc.table.default"

    table_id = fields.Many2one('migration.import.odbc.table', string="Database Table")
    model_id = fields.Many2one('ir.model', string="Model ID", related="table_id.model_id")
    field_id = fields.Many2one('ir.model.fields', string="ORM Field")
    value = fields.Char(string="Value")
    
