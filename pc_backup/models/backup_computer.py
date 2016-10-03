# -*- coding: utf-8 -*-
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
    
class BackupComputerFile(models.Model):

    _name = "backup.computer.file"
    _description = "Computer Backup File"
    
    bc_id = fields.Many2one('backup.computer', string="Computer")
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