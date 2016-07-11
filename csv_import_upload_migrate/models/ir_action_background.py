# -*- coding: utf-8 -*-
import csv
import base64
import StringIO
from datetime import datetime
import logging
import math
_logger = logging.getLogger(__name__)

from openerp import api, fields, models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class IrActionBackground(models.Model):

    _name = "ir.action.background"
    
    name = fields.Char(string="Name")
    action_file = fields.Binary(string="Action File")
    progress_current = fields.Integer(string="Progress Current")
    progress_max = fields.Integer(string="Progress Max")
    track_progress = fields.Boolean(string="Track Progress", help="Tracks how far along a action is complete(decreases speed)")
    state = fields.Selection([('started','Started'), ('finished','Finished')], default="started", string="State")
    start_time = fields.Datetime(string="Start Time")
    auto_commit = fields.Boolean(string="Auto Commit", help="Adds the records after every line is executed without waiting until the file finishes(decreases speed)", default="1")
    finish_time = fields.Datetime(string="Fnish Time")
    time_taken = fields.Char(string="Time Taken", compute="_compute_time_taken")
    rule_char_size = fields.Selection([('do_not_import_record','Do not import record'),('truncate','Truncate')], string="Exceed Max Size", default="do_not_import_record")
    log = fields.Text(string="Log")
    
    @api.depends('start_time','finish_time')
    def _compute_time_taken(self):
        if self.start_time and self.finish_time:
            start_time = datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)
            finish_time = datetime.strptime(self.finish_time, DEFAULT_SERVER_DATETIME_FORMAT)
            time_taken = finish_time - start_time
            self.time_taken = str(time_taken.seconds) + " seconds"
    
    
    @api.model
    def process_background_actions(self):
        
        for background_action in self.env['ir.action.background'].search([]):
            model = "res.partner"
            my_model = self.env['ir.model'].search([('model','=',model)])[0]
            
            log_string = ""
            background_action.start_time = datetime.utcnow()
            rownum = 0
            csv_data = base64.decodestring(background_action.action_file)
            reader = csv.reader(StringIO.StringIO(csv_data), delimiter=',')
            track = background_action.track_progress
            auto_commit = background_action.auto_commit
            cancel_import = False
            
            header = []
            header_field = {}
            for row in reader:
                row_dict = {}
                # Save header row.
                if rownum == 0:
                    header = row
                    colnum = 0
                    for col in row:
                        _logger.error(col)
                        map_column = self.env['ir.model.fields'].search([('model_id','=',my_model.id), ('name','=', col )])
                        if len(map_column) == 1:
                            header_field[colnum] = map_column[0]
                            colnum += 1
                        elif len(map_column) > 1:
                            log_string += "Column " + col + " maps to more then 1 field, import failed\n"
                            cancel_import = True
                        else:
                            log_string += "Column " + col + " could not be found\n"
                            cancel_import = True
                    
                    if cancel_import:
                        break
                else:
                    colnum = 0
                    _logger.error("row num: " + str(rownum))
                    for col in row:
                        row_dict[ header[colnum] ] = col
                        ttype = header_field[colnum].ttype
                        size = header_field[colnum].size
 
                        #Char size validation
                        if ttype == "char" and size != 0:
                            #Exceeds max size
                            if len(col) > size:
                                if background_action.rule_char_size == "do_not_import_record":
                                    log_string += "Row " + str(rownum) + " was skipped because field " + str(header[colnum]) + " exceeded the character limit\n"
                                    break
                                elif background_action.rule_char_size == "truncate":
                                    #Truncates by  default
                                    log_string += "Row " + str(rownum) + " field " + str(header[colnum]) + " was truncated\n"
                        
                        colnum += 1
  
                    self.env[model].create(row_dict)
                    
                    if track:
                        background_action.progress_current = rownum
                        
                    if auto_commit:
                        self._cr.commit()
                                    
                rownum += 1
            
            background_action.state = "finished"
            background_action.finish_time = datetime.utcnow()
            background_action.log = log_string