import httplib, urllib
from os import walk
import os
import base64
import getpass
import sys
import socket

#Load settings from file
settings = {}
with open( os.path.join(sys.path[0], "creds.sec") ) as myfile:
    for line in myfile:
        name, var = line.partition("=")[::2]
        settings[name.strip()] = var.strip('\n')

url = settings['url']
db = settings['db']
directories = settings['directories']
key = settings['key']

computer_username = getpass.getuser()
computer_name = socket.gethostname()

#Register a change
backup_change_id = urllib.urlopen(url + "/backup/client/register/change?key=" + key + "&computer_username=" + computer_username + "&computer_name=" + computer_name ).read()

backup_file_count = 0
#Backup all files in the backup directories
for backup_directory in directories.split(","):
    for (root, dirs, files) in walk(backup_directory):
        for filename in files:
            file_path = os.path.join(root, filename)

            #Encode each file into base64 and create as a file revision
            try:
                encoded_string = ""
                with open(file_path, "rb") as local_backup_file:
                    encoded_string = base64.b64encode(local_backup_file.read())

                params = urllib.urlencode({'key': key, 'change_id': backup_change_id, 'file_path': file_path, 'encoded_string': encoded_string})
                conn = httplib.HTTPConnection( url.replace("http://","") )
                headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
                conn.request("POST", "/backup/client/file/upload", params, headers)
                response = conn.getresponse()
                data = response.read()
                conn.close()

                backup_file_count += 1
                print "(" + str(backup_file_count) + ") " + file_path + " Backed Up, Revision: " + data
            except:
                print "FAILED TO BACK UP " + file_path
                
print str(backup_file_count) + " Files Backed Up"