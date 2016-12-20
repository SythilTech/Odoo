# -*- coding: utf-8 -*-
import os
import ntpath

import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class BackupComputer(models.Model):

    _name = "backup.computer"
    _description = "Computer Backup"
    
    user_id = fields.Many2one('res.users', string="User")
    username = fields.Char(string="Username", help="The user account on the computer")
    computer_identifier = fields.Char(string="Computer Identifier", help="Unique code for the PC, different computer means different backup archive for the user")
    computer_name = fields.Char(string="Computer Name", help="Display Purposes only, a user can restore files from any of thier computers")
    backup_file_ids = fields.One2many('backup.computer.file', 'bc_id', string="Backup Files")
    backup_type = fields.Selection([('full','Full Backup')], string="Backup Type", default="full")

class BackupComputerChange(models.Model):

    _name = "backup.computer.change"
    _description = "Computer Backup Change"

    bc_id = fields.Many2one('backup.computer', string="Computer")    
    new_files = fields.Integer(string="New Files")
    changed_files = fields.Integer(string="Changed Files")    
    removed_files = fields.Integer(string="Removed Files")

    @api.model
    def register_change(self, computer_username, computer_name):
        computer_backup = self.env['backup.computer'].search([('username','=',computer_username), ('computer_name','=',computer_name) ])
        
        if len(computer_backup) == 0:
            #This computer has not been backed up before so add it to the list
            computer_backup = self.env['backup.computer'].create({'user_id': self.env.user.id, 'username':computer_username, 'computer_name': computer_name })
        elif len(computer_backup) == 1:
            computer_backup = computer_backup[0]
        
        backup_change = self.env['backup.computer.change'].create({'bc_id': computer_backup.id})
        
        return backup_change.id
        
    @api.model
    def backup_file(self, change_id, file_path, file_data):

        backup_change = self.env['backup.computer.change'].browse(change_id)
        
        backup_file = self.env['backup.computer.file'].search([('bc_id', '=', backup_change.bc_id.id), ('backup_path','=',file_path)])

        if len(backup_file) == 0:
            #This file has not been backed up before so create a record for it
            backup_file = self.env['backup.computer.file'].create({'change_id': backup_change.id, 'bc_id': backup_change.bc_id.id, 'backup_path': file_path, 'file_name': ntpath.basename(file_path) })
        elif len(backup_file) == 1:
            backup_file = backup_file[0]

        #Create a new file revision
        backup_file_revision = self.env['backup.computer.file.revision'].create({'bcf_id': backup_file.id, 'backup_data': file_data})

        return backup_file_revision.id
        
class BackupComputerFile(models.Model):

    _name = "backup.computer.file"
    _description = "Computer Backup File"
    
    bc_id = fields.Many2one('backup.computer', string="Computer")
    change_id = fields.Many2one('backup.computer.change', string="Backup Change")
    revision_ids = fields.One2many('backup.computer.file.revision', 'bcf_id', string="File Revisions")
    file_name = fields.Char(string="File Name")
    backup_path = fields.Char(string="Backup Path", help="The file path on the backup pc")

class BackupComputerFileRevision(models.Model):

    _name = "backup.computer.file.revision"
    _description = "Computer Backup File Revision"
    _order = "create_date desc"
    
    bcf_id = fields.Many2one('backup.computer.file', string="Computer Backup File")
    backup_data = fields.Binary(string="Backup Data")
    backup_data_filename = fields.Char(string="Backup Data Filename", related="bcf_id.file_name")
    type = fields.Selection([('creation','Creation'),('change','Change'),('deletion','Deletion') ] , string="Type", default="creation")