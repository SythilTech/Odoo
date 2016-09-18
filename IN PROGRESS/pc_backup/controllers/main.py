# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
import openerp
import tempfile
import zipfile
import os

import openerp.http as http
from openerp.http import request

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
	    client_directory = module_directory + "/client/windows/backup_client"
	    for dirname, subdirs, files in os.walk(client_directory):
                for filename in files:
                    full_path = os.path.join(dirname, filename)
                    zf.write(full_path, os.path.relpath(full_path, client_directory) )
        
            #Write the crential file to the zip
            cred_string = ""
            cred_string += "url=" + request.httprequest.host_url + "\n"
            cred_string += "login=" + request.env.user.login            
            zf.writestr('creds.sec', cred_string)

        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', "attachment; filename=Odoo_Backup_Client.zip" ),
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
            return http.request.render('pc_backup.list_files', {'user_machine': user_machine})
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