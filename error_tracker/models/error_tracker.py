# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ErrorTracker(models.TransientModel):

    _name = "error.tracker"
    _order = 'line_number desc'
    
    error_date = fields.Datetime(string='Date')
    level = fields.Selection([('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], string="Level")
    database = fields.Char(string="Database")
    error_class = fields.Char(string="Class")
    class_error = fields.Char(string="Class Error")
    error_content = fields.Text(string="Error Content")
    line_number = fields.Integer(string="Line Number")

    @api.one
    def read_local_log(self):
        
        log_path = "/var/log/odoo/odoo-server.log"
        
        with open(log_path) as f:
            lines = f.readlines()
            
        line_number = 0
        error_content = ""
        for line in lines:
            line_number += 1
            if " INFO " in line or " WARNING " in line or " ERROR " in line or " CRITICAL " in line:
                if error_content <> "":
                   log_entry.error_content = error_content
                   error_content = ""
                
                error_date = line.split(' ')[0] + " " + line.split(' ')[1].split(",")[0]
                level = line.split(' ')[3]
                database = line.split(' ')[4]
                error_class = line.split(' ')[5][:-1]
                class_error = line.split(":")[3]
                
                log_entry = self.env['error.tracker'].create({'line_number': line_number, 'error_date':  error_date, 'level': level, 'database': database, 'error_class': error_class, 'class_error': class_error})
            else:
                error_content += line
            