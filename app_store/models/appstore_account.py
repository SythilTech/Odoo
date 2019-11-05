# -*- coding: utf-8 -*
import io
import zipfile
import tempfile
from urllib.request import Request, urlopen
import os
from io import BytesIO
import sys
from os import walk
import glob
from lxml import html, etree
import csv
import fnmatch
import logging
_logger = logging.getLogger(__name__)
import ast
import base64
import os.path
from docutils.core import publish_string
import json

from odoo import api, fields, models

class AppstoreAccount(models.Model):

    _name = "appstore.account"
    _description = "App Store Account"

    name = fields.Char(string="Name")
    repositories_ids = fields.One2many('appstore.account.repository', 'asa_id', string="Repositories")

    def sync_repos(self):
        self.env['appstore.account.repository'].check_all_repositories()

class AppstoreAccountRepository(models.Model):

    _name = "appstore.account.repository"
    _description = "App Store Account Repository"

    asa_id = fields.Many2one('appstore.account', ondelete='cascade', string="App Store Account")
    url = fields.Char(string="Repository URL")
    token = fields.Char(String="Token")

    @api.model
    def check_all_repositories(self):
        """Checks to see if there are any new modules"""

        filename = tempfile.mktemp('.zip')
        destDir = tempfile.mktemp()
        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"

        for account_repository in self.env['appstore.account.repository'].search([]):
            rep_directory = app_directory + "/" +  account_repository.url.split("/")[3]

            repository_url = account_repository.url.split("#")[0] + "/archive/" + account_repository.url.split("#")[1] + ".zip"
            q = Request(repository_url)
            
            if account_repository.token:
                q.add_header('Authorization', 'token ' + account_repository.token)

            try:
                repo_data = urlopen(q).read()
            except:
                _logger.error("Failed to read repo")
                continue

            thefile = zipfile.ZipFile(BytesIO(repo_data))

            if not os.path.exists(rep_directory):
                os.makedirs(rep_directory)

            thefile.extractall(rep_directory)

            thefile.close()

            rep_name = account_repository.url.split("/")[4].replace("#","-")

            full_rep_path = rep_directory + "/" + rep_name

            #Go through all module folders under the repository directory and analyse the module
            for dir in os.listdir(full_rep_path):
                if os.path.isdir(os.path.join(full_rep_path, dir)):
                    self.analyse_module(dir, full_rep_path)

    def analyse_module(self, module_name, app_directory):
        try:
            manifest_file = ""
            if os.path.exists(app_directory + "/" + module_name + "/__manifest__.py"):
                manifest_file = "__manifest__.py"

            if os.path.exists(app_directory + "/" + module_name + "/__openerp__.py"):
                manifest_file = "__openerp__.py"        

            if manifest_file == "":
                #If they module does not have a manifest file do not even bother
                return 0

            with open(app_directory + "/" + module_name + "/" + manifest_file, 'r') as myfile:
                #Remove comments as literal_eval hates them
                trimmed_data = ""
                for i, line in enumerate(myfile):
                    if not line.lstrip().startswith("#"):
                        trimmed_data += line
                        
                #trimmed_data = trimmed_data.replace("'", "\"")
                op_settings = ast.literal_eval(trimmed_data)


            #Modules that don't have version number are not analysed
            if 'version' not in op_settings:
                return 0

            #Convert icon file to base64
            icon_base64 = ""
            if os.path.isfile(app_directory + "/" + module_name + "/static/description/icon.png"):
                with open(app_directory + "/" + module_name + "/static/description/icon.png", "rb") as image_file:
                    icon_base64 = base64.b64encode(image_file.read())

            if self.env['module.overview'].search_count([('name', '=', module_name)]) == 0:
                module_overview = self.env['module.overview'].create({'name': module_name})
            else:
                #Clear out most things except download / view count
                module_overview = self.env['module.overview'].search([('name', '=', module_name)])[0]
                module_overview.models_ids.unlink()
                module_overview.menu_ids.unlink()
                module_overview.group_ids.unlink()
                module_overview.image_ids.unlink()
                module_overview.depend_ids.unlink()

            if 'author' in op_settings:
                module_overview.author = op_settings['author']

            if 'summary' in op_settings:
                module_overview.summary = op_settings['summary']

            module_overview.module_name = op_settings['name']
            module_overview.icon = icon_base64
            module_overview.version = op_settings['version']

        except Exception as e:
            _logger.error(module_name)
            _logger.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error("Line: " + str(exc_tb.tb_lineno) )

        try:
            #Read /doc/changelog.rst file
            if os.path.exists(app_directory + "/" + module_name + "/doc/changelog.rst"):
                with open(app_directory + "/" + module_name + "/doc/changelog.rst", 'r') as changelogfile:
                    changelogdata = changelogfile.read()
                    module_overview.change_log_raw = changelogdata
                    module_overview.change_log_html = changelogdata
                    #module_overview.change_log_html = publish_string(changelogdata, writer_name='html').split("\n",2)[2]

            #Read /static/description/index.html file
            if os.path.exists(app_directory + "/" + module_name + "/static/description/index.html"):
                with open(app_directory + "/" + module_name + "/static/description/index.html", 'r') as descriptionfile:
                    descriptiondata = descriptionfile.read()
                    module_overview.store_description = descriptiondata

            if 'depends' in op_settings:
                for depend in op_settings['depends']:
                    self.env['module.overview.depend'].create({'mo_id': module_overview.id, 'name': depend})

            if 'images' in op_settings:
                for img in op_settings['images']:
                    image_path = app_directory + "/" + module_name + "/" + img
                    if os.path.exists(image_path):
                        with open(image_path, "rb") as screenshot_file:
                            screenshot_base64 = base64.b64encode(screenshot_file.read())

                        self.env['module.overview.image'].create({'mo_id': module_overview.id, 'name': img, 'file_data': screenshot_base64})

            for root, dirnames, filenames in os.walk(app_directory + '/' + module_name):
                for filename in fnmatch.filter(filenames, '*.xml'):
                    self._read_xml(os.path.join(root, filename), module_overview.id)

                #for filename in fnmatch.filter(filenames, '*.csv'):
                #    self._read_csv(filename, open( os.path.join(root, filename) ).read(), module_overview.id)

        except Exception as e:
            _logger.error(module_name)
            _logger.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error("Line: " + str(exc_tb.tb_lineno) )
            pass

        #Create a zip of the module (TODO include dependacies)
        zf = zipfile.ZipFile(os.path.expanduser('~') + "/apps/" + module_name + ".zip", "w")
        for dirname, subdirs, files in os.walk(app_directory + "/" + module_name):
            for filename in files:
                full_file_path = os.path.join(dirname, filename)
                zf.write(full_file_path, arcname=os.path.relpath(full_file_path, app_directory + "/" + module_name))
        zf.close()
                        
    def _read_csv(self, file_name, file_content, m_id):
        if "ir.model.access":
            rownum = 0
            reader = csv.reader(file_content, delimiter=',')
            header = []
            for row in reader:
                row_dict = {'mo_id': m_id}
                # Save header row.
                if rownum == 0:
                    header = row
                else:
                    colnum = 0
                    for col in row:
                         #map the csv header columns to the fields 
                         if header[colnum] == "id":
                             row_dict['x_id'] = col
                         elif header[colnum] == "model_id:id":
                             row_dict['model'] = col
                         elif header[colnum] == "group_id:id":
                             row_dict['group'] = col
                         elif header[colnum] == "perm_read":
                             row_dict['perm_read'] = bool(int(col))
                         elif header[colnum] == "perm_write":
                             row_dict['perm_write'] = bool(int(col))
                         elif header[colnum] == "perm_create":
                             row_dict['perm_create'] = bool(int(col))
                         elif header[colnum] == "perm_unlink":
                             row_dict['perm_unlink'] = bool(int(col))
                         else:
                             row_dict[header[colnum]] = col

                         colnum += 1

                    group_name = ""

                    #Deal with blank or other malformed rows
                    if ('group' not in row_dict) or ('x_id' not in row_dict):
                        continue

                    if row_dict['group'] != "":
                        group_name = self.env['ir.model.data'].get_object(row_dict['group'].split(".")[0], row_dict['group'].split(".")[1]).display_name

                    #Create the group if it does exist
                    ex_group = self.env['module.overview.group'].search([('x_id','=',row_dict['group'])])

                    if len(ex_group) == 0:
                        my_group = self.env['module.overview.group'].create({'mo_id': m_id, 'name': group_name, 'x_id': row_dict['group']})
                    else:
                        my_group = ex_group[0]

                    #If model diiesn't exists, create it
                    ex_model = self.env['module.overview.model'].search([('name','=', self._ref_to_model(row_dict['model']) )])

                    if len(ex_model) == 0:
                        #create the model
                        my_model = self.env['module.overview.model'].create({'name':self._ref_to_model(row_dict['model']), 'mo_id': m_id})
                    else:
                        my_model = ex_model[0]

                    #Add the access rule to the group
                    self.env['module.overview.group.access'].create({'mog_id':my_group.id, 'model_id': my_model.id, 'perm_read': row_dict['perm_read'], 'perm_write':row_dict['perm_write'], 'perm_create':row_dict['perm_create'], 'perm_unlink':row_dict['perm_unlink']})

                    access_dict = {'model_id':my_model.id, 'name': group_name, 'x_id': row_dict['group'], 'perm_read': row_dict['perm_read'], 'perm_write':row_dict['perm_write'], 'perm_create':row_dict['perm_create'], 'perm_unlink':row_dict['perm_unlink']}
                    self.env['module.overview.model.access'].create(access_dict)

                rownum += 1

    def _ref_to_model(self, ref_string):
        """Turns 'model_sms_message' into 'sms.message'"""
        return ref_string.replace("model_","").replace("_",".")

    def _read_xml(self, file_path, m_id):
        return_string = ""
        root = etree.parse(file_path)

        insert_menu = root.xpath('//menuitem')
        for menu in insert_menu:
            menu_dict = {'mo_id': m_id}
            menu_dict['x_id'] = menu.attrib['id']

            if 'name' in menu.attrib:
                menu_dict['name'] = menu.attrib['name']

            if 'parent' in menu.attrib:
                try:
                    menu_dict['parent'] = self.env['ir.model.data'].get_object(menu.attrib['parent'].split(".")[0], menu.attrib['parent'].split(".")[1]).display_name
                except:
                    pass
                menu_dict['parent_x_id'] = menu.attrib['parent']

            self.env['module.overview.menu'].create(menu_dict)

        insert_records = root.xpath('//record')
        for rec in insert_records:
            record_id = rec.attrib['id']

            #If it's a view
            if rec.attrib['model'] == "ir.ui.view":
                if len(rec.find(".//field[@name='name']")) > 0:
                    record_name = rec.find(".//field[@name='name']").text
                else:
                    continue

                model_name = rec.find(".//field[@name='model']").text
                model_exist = self.env['module.overview.model'].search([('name','=',model_name),('mo_id','=',m_id) ])
                model = ""

                #if this is the first time encountering model, create it.
                if len(model_exist) == 0:
                    model = self.env['module.overview.model'].create({'mo_id': m_id, 'name': model_name})
                else:
                    model = model_exist[0]

                #add this view to this model
                self.env['module.overview.model.view'].create({'model_id': model.id, 'name': record_name, 'x_id': record_id})