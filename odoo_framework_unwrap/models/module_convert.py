# -*- coding: utf-8 -*

import pyodbc
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models
from odoo.exceptions import UserError

class ModuleConvert(models.Model):

    _name = "module.convert"
    _description = "Module Convert"

    module_id = fields.Many2one('ir.module.module', string="Module")
    database_id = fields.Many2one('module.convert.database', string="Database")
    language_id = fields.Many2one('module.convert.language', string="Language")
    mode = fields.Selection([('overwrite','Overwrite')], default="overwrite", string="Mode")
    dsn_id = fields.Many2one('module.convert.dsn', string="Driver")
    connection_string_template_id = fields.Many2one('module.convert.connect', string="Connection Template")
    connection_string = fields.Char(string="Connection String", help="See https://www.connectionstrings.com if you want a connection string other then MySQL")
    connect_server = fields.Char(string="Server")
    connect_database = fields.Char(string="Database")
    connect_username = fields.Char(string="Username")
    connect_password = fields.Char(string="Password")

    @api.onchange('connection_string_template_id','dsn_id','connect_server','connect_database','connect_username','connect_password')
    def _onchange_dsn_id(self):
        if self.dsn_id and self.connection_string_template_id.connection_string:
            cs = self.connection_string_template_id.connection_string

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
        for dsn in dsns:
            if self.env['module.convert.dsn'].search_count([('name','=',dsn)]) == 0:
                self.env['module.convert.dsn'].create({'name': dsn, 'driver': sources[dsn]})

    def test_connection(self):
        conn = pyodbc.connect(self.connection_string)
        conn.close()
        
        #pyodbc will provide most of the error reporting so if you got here I can assume everything went well
        raise UserError("Connection Successful")

    def convert_models(self):

        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()

        # Only convert models that are exclusively owned by the selected module (modules field is not searchable)
        for model_data in self.env['ir.model.data'].search([('module', '=', self.module_id.name), ('model', '=', 'ir.model')]):
            model = self.env['ir.model'].browse(model_data.res_id)
            if model.modules == self.module_id.name:
                
                if self.mode == "overwrite":
                    cursor.execute("DROP TABLE IF EXISTS `" + model.model.replace(".","_") + "`;")
                    sql = self.env['module.convert.database.' + self.database_id.internal_name].convert_model(model, self.module_id.name)
                    cursor.execute(sql)

class ModuleConvertDSN(models.Model):

    _name = "module.convert.dsn"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")
    connection_string = fields.Char(string="Connect String")

class ModuleConvertConnect(models.Model):

    _name = "module.convert.connect"

    name = fields.Char(string="Name")
    driver = fields.Char(string="Driver")
    connection_string = fields.Char(string="Connect String")

class ModuleConvertDatabase(models.Model):

    _name = "module.convert.database"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name")

class ModuleConvertDatabaseMySQL(models.Model):

    _name = "module.convert.database.mysql"

    def convert_model(self, model, module_name):
        sql = ""
        table_name = model.model.replace(".","_")

        sql += "CREATE TABLE `" + table_name + "` ("

        # Only convert fields that were created by the selected module
        for field in self.env['ir.model.fields'].search([('model_id', '=', model.id)]):
            if module_name in field.modules.split(","):
                if field.name == "id":
                    sql += "id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
                elif field.ttype == "char":
                    #psql varchar to mySQl varchar
                    sql += "`" + field.name + "` varchar(255) NOT NULL,"

        sql = sql[:-1]
        sql += ") ENGINE=InnoDB DEFAULT CHARSET=utf8;"
        return sql

class ModuleConvertLanguage(models.Model):

    _name = "module.convert.language"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name")