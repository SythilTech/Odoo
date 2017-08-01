# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
import openerp
import tempfile
import zipfile
import os
import string
import random
import ntpath
import hashlib
import os.path
import openerp.http as http
from openerp.http import request
import difflib
import logging
_logger = logging.getLogger(__name__)

from openerp.addons.website.models.website import slug

class BackupController(http.Controller):

    @http.route('/backup/client/download', type="http", auth="user")
    def backup_client_download(self, **kw):
        """Page logged in users can download thier specific version of backup client"""
        return http.request.render('pc_backup.download_client', {})

    @http.route('/backup/client/download/file', type="http", auth="user")
    def backup_client_download_file(self, **kw):
        """Bundle the login creds with the module"""

        t = tempfile.TemporaryFile()
        module_directory = openerp.modules.get_module_path("pc_backup")

        with zipfile.ZipFile(t, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
	    client_directory = module_directory + "/client/windows/binary"
	    for dirname, subdirs, files in os.walk(client_directory):
                for filename in files:
                    full_path = os.path.join(dirname, filename)
                    zf.write(full_path, os.path.relpath(full_path, client_directory) )
        
            #Write the crential file to the zip
            cred_string = ""
            cred_string += "url=" + request.httprequest.host_url[:-1] + "\n"
            cred_string += "db=" + request.env.cr.dbname + "\n"
            cred_string += "last-backup-time=1970-01-01 01:01:01\n"
            cred_string += "directories=C:\backup1,C:\backup2\n"

            api_key = ""
            
            if request.env.user.backup_key:
                api_key = request.env.user.backup_key
            else:
                #Generate a random API key
                api_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))
                request.env.user.backup_key = api_key
                
            cred_string += "key=" + api_key

            zf.writestr('creds.sec', cred_string)

        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', request.env['ir.http'].content_disposition("Odoo Backup Client.zip") ),
        ]

        t.seek(0)
        response = werkzeug.wrappers.Response(t, headers=headers, direct_passthrough=True)
        return response        

    @http.route('/backup/client/machines', type="http", auth="user")
    def backup_client_machines(self, **kw):
        """Displays all machines owned by this user"""
        user_machines = request.env['backup.computer'].search([('user_id','=',request.env.user.id)])
        return http.request.render('pc_backup.list_machines', {'user_machines': user_machines})
        
    @http.route('/backup/client/machines/<machine_id>', type="http", auth="user")
    def backup_client_machines_files(self, machine_id, **kw):
        """Displays all files for the selected machine"""
        user_machine = request.env['backup.computer'].browse( int(machine_id) )
        
        #Check if the machine is owned by the user
        if user_machine.user_id.id == request.env.user.id:
            changelog = request.env['backup.computer.change'].sudo().search([('bc_id', '=', user_machine.id)], order="create_date desc")
            return http.request.render('pc_backup.list_files', {'user_machine': user_machine, 'changelog': changelog})
        else:
            return "Not your machine!!!"

    @http.route('/backup/client/changelog/<change_id>', type="http", auth="user")
    def backup_client_changelog(self, change_id, **kw):
        """Displays the files that where changed during this change entry"""
        change_id = request.env['backup.computer.change'].browse( int(change_id) )
        
        #Check if the change is owned by the user
        if change_id.bc_id.user_id.id == request.env.user.id:
            return http.request.render('pc_backup.changelog', {'changelog': change_id})
        else:
            return "Not your machine!!!"
            
    @http.route('/backup/client/machines/<machine_id>/<file_id>', type="http", auth="user")
    def backup_client_machines_revisions(self, machine_id, file_id, **kw):
        """Displays all revisions of the file"""
        user_file = request.env['backup.computer.file'].browse( int(file_id) )
        
        #Check if the file is owned by the user
        if user_file.bc_id.user_id.id == request.env.user.id:
            return http.request.render('pc_backup.list_revisions', {'user_file': user_file})
        else:
            return "Not your File!!!"

            
    @http.route('/backup/client/machines/<machine_id>/<file_id>/<revision_id>', type="http", auth="user")
    def backup_client_machines_revision_download(self, machine_id, file_id, revision_id, **kw):
        """Downloads the file revision"""
        user_revision = request.env['backup.computer.file.revision'].browse( int(revision_id) )
        
        #Check if the file is owned by the user
        if user_revision.bcf_id.bc_id.user_id.id == request.env.user.id:

            headers = [
                ('Content-Type', 'application/octet-stream; charset=binary'),
                ('Content-Disposition', request.env['ir.http'].content_disposition(user_revision.backup_data_filename) ),
            ]

            filecontent = base64.b64decode(user_revision.backup_data)
            return request.make_response(filecontent, headers=headers)

        else:
            return "Not your File!!!"

    @http.route('/backup/client/machines/<machine_id>/<file_id>/<revision_id>/diff', type="http", auth="user")
    def backup_client_machines_revision_diff(self, machine_id, file_id, revision_id, **kw):
        """Difference between this and the previous file revision"""
        user_revision = request.env['backup.computer.file.revision'].browse( int(revision_id) )
        
        #Check if the file is owned by the user
        if user_revision.bcf_id.bc_id.user_id.id == request.env.user.id:

            previous_revision = request.env['backup.computer.file.revision'].search([('bcf_id','=', user_revision.bcf_id.id ), ('create_date','<', user_revision.create_date)], order="create_date desc", limit=1)[0]
            previous_data = base64.b64decode(previous_revision.backup_data).strip().splitlines()
            current_data = base64.b64decode(user_revision.backup_data).strip().splitlines()
            diff_text = ""
            diff_counter = 0
            
            for line in difflib.unified_diff(previous_data, current_data, fromfile='file1', tofile='file2'):
                
                if diff_counter >= 3:
                    diff_text += line + "<br/>\n"
                
                diff_counter += 1
    
            return diff_text

        else:
            return "Not your File!!!"

    @http.route('/backup/client/register/change', type='http', auth="public", methods=['GET'], csrf=False)        
    def backup_client_register_change(self, key, computer_username, computer_name):
        backup_user = request.env['res.users'].sudo().search([('backup_key', '=', key)])[0]
        computer_backup = request.env['backup.computer'].sudo().search([('username','=',computer_username), ('computer_name','=',computer_name) ])
        
        if len(computer_backup) == 0:
            #This computer has not been backed up before so add it to the list
            computer_backup = request.env['backup.computer'].sudo().create({'user_id': backup_user.id, 'username':computer_username, 'computer_name': computer_name})
        elif len(computer_backup) == 1:
            computer_backup = computer_backup[0]
        
        backup_change = request.env['backup.computer.change'].sudo().create({'bc_id': computer_backup.id})
        
        return str(backup_change.id)

    @http.route('/backup/client/file/upload', type='http', auth="public", methods=['POST'], csrf=False)
    def backup_client_backup_file(self, key, change_id, file_path, encoded_string):

        backup_user = request.env['res.users'].sudo().search([('backup_key', '=', key)])[0]
        backup_change = request.env['backup.computer.change'].sudo().browse( int(change_id) )

        if backup_change.bc_id.user_id.id == backup_user.id:
            backup_file = request.env['backup.computer.file'].sudo().search([('bc_id', '=', backup_change.bc_id.id), ('backup_path','=',file_path)])

            if len(backup_file) == 0:
                #This file has not been backed up before so create a record for it
                backup_file = request.env['backup.computer.file'].sudo().create({'change_id': backup_change.id, 'bc_id': backup_change.bc_id.id, 'backup_path': file_path, 'file_name': ntpath.basename(file_path) })
            elif len(backup_file) == 1:
                backup_file = backup_file[0]

            #Only create a revision if the file has changed
            md5_hash = hashlib.md5(encoded_string).hexdigest()
            
            if request.env['backup.computer.file.revision'].sudo().search_count([('bcf_id', '=', backup_file.id)]) > 0:
                last_revision = request.env['backup.computer.file.revision'].sudo().search([('bcf_id', '=', backup_file.id)], order="create_date desc", limit=1)

                if md5_hash != last_revision.md5_hash: 

                    #The file has changed so create a new revision
                    backup_mode = request.env['ir.values'].get_default('backup.settings', 'backup_mode')
                    backup_file_revision = request.env['backup.computer.file.revision'].sudo().create({'change_id': backup_change.id, 'bcf_id': backup_file.id, 'backup_data': encoded_string, 'md5_hash': md5_hash, 'backup_mode': 'full', 'diff_text': diff_text})
                    backup_change.changed_files += 1
                    

                    
                
                    return str(backup_file_revision.id)
                else:
                    #File hasn't changed so don't write a revision to save space
                    return 0
            else:
                #File has not been backed up before so crate the first revision
                backup_file_revision = request.env['backup.computer.file.revision'].sudo().create({'change_id': backup_change.id, 'bcf_id': backup_file.id, 'backup_data': encoded_string, 'md5_hash': md5_hash})

                backup_change.new_files += 1

                return str(backup_file_revision.id)
                


            
        else:
            #Trying to backup to someone elses computer?!?
            return "Error incorrect account"