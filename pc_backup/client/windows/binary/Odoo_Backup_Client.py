import clr
import xmlrpclib
import sys
import System
from os import walk
import os
import base64
import webbrowser

clr.AddReference('System.Drawing')
clr.AddReference('System.Windows.Forms')

from System.Drawing import *
from System.Windows.Forms import *

class MyForm(Form):
    def __init__(self):
        # Create child controls and initialize form
        self.Text = "Odoo Backup Client"
        self.Width = 400

        self.label1 = Label()
        self.label1.Text = "Odoo URL"
        self.label1.Location = Point(20, 20)
        self.Controls.Add(self.label1)

        self.urlTextbox = TextBox()
        self.urlTextbox.Location = Point(140, 20)
        self.urlTextbox.Width = 200
        self.Controls.Add(self.urlTextbox)

        self.label2 = Label()
        self.label2.Text = "Username"
        self.label2.Location = Point(20, 50)
        self.Controls.Add(self.label2)

        self.usernameTextbox = TextBox()
        self.usernameTextbox.Location = Point(140, 50)
        self.usernameTextbox.Width = 200
        self.Controls.Add(self.usernameTextbox)

        self.label3 = Label()
        self.label3.Text = "Password"
        self.label3.Location = Point(20, 80)
        self.Controls.Add(self.label3)

        self.passwordTextbox = TextBox()
        self.passwordTextbox.Location = Point(140, 80)
        self.passwordTextbox.Width = 200
        self.Controls.Add(self.passwordTextbox)

        self.label4 = Label()
        self.label4.Text = "Directory to Backup"
        self.label4.Location = Point(20, 110)
        self.label4.Width = 120
        self.Controls.Add(self.label4)

        self.backupDirectoryTextbox = TextBox()
        self.backupDirectoryTextbox.Location = Point(140, 110)
        self.backupDirectoryTextbox.Width = 200
        self.Controls.Add(self.backupDirectoryTextbox)

        self.label5 = Label()
        self.label5.Text = "Database"
        self.label5.Location = Point(20, 140)
        self.Controls.Add(self.label5)

        self.databaseTextbox = TextBox()
        self.databaseTextbox.Location = Point(140, 140)
        self.databaseTextbox.Width = 200
        self.Controls.Add(self.databaseTextbox)

        self.backupButton = Button()
        self.backupButton.Text = 'Backup Files'
        self.backupButton.Location = Point(245, 170)
        self.backupButton.Width = 95
        self.backupButton.Click += self.backup
        self.Controls.Add(self.backupButton)

        self.restoreButton = Button()
        self.restoreButton.Text = 'Restore Files'
        self.restoreButton.Location = Point(140, 170)
        self.restoreButton.Width = 95
        self.restoreButton.Click += self.restore
        self.Controls.Add(self.restoreButton)

        #Load settings from file
        settings = {}
        with open("creds.sec") as myfile:
            for line in myfile:
                name, var = line.partition("=")[::2]
                settings[name.strip()] = var.strip('\n')

        if 'url' in settings: self.urlTextbox.Text = settings['url']
        if 'login' in settings: self.usernameTextbox.Text = settings['login']
        if 'db' in settings: self.databaseTextbox.Text = settings['db']
        if 'password' in settings: self.passwordTextbox.Text = settings['password']
        if 'backup' in settings: self.backupDirectoryTextbox.Text = settings['backup']

    def restore(self, sender, event):
        url = self.urlTextbox.Text + "/backup/client/machines"
        webbrowser.open(url)

    def backup(self, sender, event):
        url = self.urlTextbox.Text
        db = self.databaseTextbox.Text
        username = self.usernameTextbox.Text
        password = self.passwordTextbox.Text
        backup_directory = self.backupDirectoryTextbox.Text

        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        
        if uid == False:
            MessageBox.Show("Login Failed")
            return 0

        models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

        computer_name = System.Environment.MachineName
        computer_username = System.Security.Principal.WindowsIdentity.GetCurrent().Name
        
        backup = models.execute_kw(db, uid, password,'backup.computer', 'search_read',[[('user_id', '=', uid), ('username','=',computer_username), ('computer_name', '=', computer_name)]])

        #If this is the first backup then create the backup placeholder
        if backup.Count == 0:
            backup_id = models.execute_kw(db, uid, password, 'backup.computer', 'create', [{
                'user_id': uid,
                'username': computer_username,
                'computer_name': computer_name,
            }])
        else:
            backup_id = backup[0]['id']


        backup_file_count = 0
        #Backup all files in the backup directory
        for (root, dirs, files) in walk(backup_directory):
            for filename in files:
                file_path = os.path.join(root, filename)

                backup_file = models.execute_kw(db, uid, password,'backup.computer.file', 'search_read',[[('bc_id', '=', backup_id), ('backup_path','=',file_path)]])
               
                #If this file has not been backup up yet then create a backup file placeholder
                if backup_file.Count == 0:
                    backup_file_id = models.execute_kw(db, uid, password, 'backup.computer.file', 'create', [{
                        'bc_id': backup_id,
                        'file_name': filename,
                        'backup_path': file_path,
                    }])
                else:
                    backup_file_id = backup_file[0]['id']

                #Encode each file into base64 and create as a file revision
                with open(file_path, "rb") as local_backup_file:
                    encoded_string = base64.b64encode(local_backup_file.read())
                    id = models.execute_kw(db, uid, password, 'backup.computer.file.revision', 'create', [{
                        'bcf_id': backup_file_id,
                        'backup_data': encoded_string,
                    }])

                backup_file_count += 1
                
        MessageBox.Show(backup_file_count.ToString() + " Files Backed Up")   

Application.EnableVisualStyles()
Application.SetCompatibleTextRenderingDefault(False)

form = MyForm()
Application.Run(form)
