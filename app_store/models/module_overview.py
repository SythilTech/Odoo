# -*- coding: utf-8 -*
import os
from os import walk
import glob
from lxml import html, etree
import csv
import fnmatch
import zipfile
import logging
import ast
import base64
_logger = logging.getLogger(__name__)
import os.path
from docutils.core import publish_string
import sys
import json

from openerp import api, fields, models

class ModuleOverview(models.Model):

    _name = "module.overview"
    _description = "Module Overview"

    name = fields.Char(string="Internal Name")
    models_ids = fields.One2many('module.overview.model', 'mo_id', string="Models")
    model_count = fields.Integer(string="Model Count", compute="_compute_model_count")
    menu_ids = fields.One2many('module.overview.menu', 'mo_id', string="Menus")
    menu_count = fields.Integer(string="Menu Count", compute="_compute_menu_count")
    group_ids = fields.One2many('module.overview.group', 'mo_id', string="Groups")
    group_count = fields.Integer(string="Group Count", compute="_compute_group_count")
    depend_ids = fields.One2many('module.overview.depend', 'mo_id', string="Module Dependacies")
    image_ids = fields.One2many('module.overview.image', 'mo_id', string="Images")
    store_views_ids = fields.One2many('module.overview.store.view', 'mo_id', string="Store Views")
    module_view_count = fields.Integer(string="Module View Count", help="The amount of times the page for this module has been viewed")
    module_download_count = fields.Integer(string="Module Download Count", help="The amount of times this module has been downloaded")
    module_name = fields.Char(string="Module Name")
    version = fields.Char(string="Version Number")
    author = fields.Char(string="Author")
    summary = fields.Char(string="summary")
    icon = fields.Binary(string="Icon")
    store_description = fields.Html(string="Store Description")
    change_log_raw = fields.Text(string="Change Log")
    change_log_html = fields.Html(string="Change Log(html)")
    published = fields.Boolean(string="Published", default=True)

    @api.one
    @api.depends('menu_ids')
    def _compute_menu_count(self):
        self.menu_count = len(self.menu_ids)

    @api.one
    @api.depends('group_ids')
    def _compute_group_count(self):
        self.group_count = len(self.group_ids)

    @api.one
    @api.depends('models_ids')
    def _compute_model_count(self):
        self.model_count = len(self.models_ids)

class ModuleOverviewStoreView(models.Model):

    _name = "module.overview.store.view"
    _description = "Module Overview Store View"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    ip = fields.Char(string="IP")
    ref = fields.Char(string="Ref", help="The URL the person came from")
    header = fields.Char(string="Header", help="The raw header which misc info can be extracted from")

class ModuleOverviewDepend(models.Model):

    _name = "module.overview.depend"
    _description = "Module Overview Dependacies"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    name = fields.Char(string="name")

class ModuleOverviewImage(models.Model):

    _name = "module.overview.image"
    _description = "Module Overview Image"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    name = fields.Char(string="File Path")
    file_data = fields.Binary(string="File Data")

class ModuleOverviewWizard(models.Model):

    _name = "module.overview.wizard"
    _description = "Module Overview Wizard"

    name = fields.Char(string="Module Name")

    @api.one
    def update_module_list(self):
        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"

        #Go through all module folders under '~/apps' and analyse the module
        for dir in os.listdir(app_directory):
            if os.path.isdir(os.path.join(app_directory, dir)):
                try:
                    self.analyse_module(dir, app_directory)
                except Exception as e:
                    #Timeout
                    _logger.error(e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    _logger.error("Line: " + str(exc_tb.tb_lineno) )
                
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

            #Create a zip of the module (TODO include dependacies)
            zf = zipfile.ZipFile(os.path.expanduser('~') + "/apps/" + module_name + ".zip", "w")
            for dirname, subdirs, files in os.walk(app_directory + "/" + module_name):
                for filename in files:
                    full_file_path = os.path.join(dirname, filename)
                    zf.write(full_file_path, arcname=os.path.relpath(full_file_path, app_directory + "/" + module_name))
            zf.close()

        except Exception as e:
            _logger.error(module_name)
            _logger.error(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error("Line: " + str(exc_tb.tb_lineno) )
                        
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

                record_name = rec.find(".//field[@name='name']").text
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

class ModuleOverviewGroup(models.Model):

    _name = "module.overview.group"
    _description = "Module Overview Group"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    x_id = fields.Char(string="XML ID")
    name = fields.Char(string="Name")
    access_ids = fields.One2many('module.overview.group.access', 'mog_id', string="Group Permissions")

class ModuleOverviewGroupAccess(models.Model):

    _name = "module.overview.group.access"

    mog_id = fields.Many2one('module.overview.group', string="Module Overview", ondelete="cascade")
    model_id = fields.Many2one('module.overview.model', string="Model")
    perm_read = fields.Boolean(string="Read Permmision")
    perm_write = fields.Boolean(string="Write Permmision")
    perm_create = fields.Boolean(string="Create Permmision")
    perm_unlink = fields.Boolean(string="Delete Permmision")
    access_string = fields.Char(string="Access String", compute="_compute_access_string")

    @api.one
    @api.depends('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
    def _compute_access_string(self):
        a_string = ""

        if self.perm_read:
            a_string += "Read, "

        if self.perm_write:
            a_string += "Write, "

        if self.perm_create:
            a_string += "Create, "

        if self.perm_unlink:
            a_string += "Delete, "

        self.access_string = a_string[:-2]

class ModuleOverviewAccess(models.Model):

    _name = "module.overview.access"
    _description = "depricted"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    x_id = fields.Char(string="XML ID")
    name = fields.Char(string="Name")
    model = fields.Char(string="Model")
    group = fields.Char(string="Group")
    perm_read = fields.Boolean(string="Read Permmision")
    perm_write = fields.Boolean(string="Write Permmision")
    perm_create = fields.Boolean(string="Create Permmision")
    perm_unlink = fields.Boolean(string="Delete Permmision")
    access_string = fields.Char(string="Access String", compute="_compute_access_string")

    @api.one
    @api.depends('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
    def _compute_access_string(self):
        a_string = ""

        if self.perm_read:
            a_string += "Read, "

        if self.perm_write:
            a_string += "Write, "

        if self.perm_create:
            a_string += "Create, "

        if self.perm_unlink:
            a_string += "Delete, "

        self.access_string = a_string[:-2]

class ModuleOverviewMenu(models.Model):

    _name = "module.overview.menu"
    _description = "Module Overview Menu"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    name = fields.Char(string="Name")
    x_id = fields.Char(string="XML ID")
    parent = fields.Char(string="Parent Menu")
    parent_x_id = fields.Char(string="Parent Menu XML ID")

class ModuleOverviewModel(models.Model):

    _name = "module.overview.model"
    _description = "Module Overview Model"

    mo_id = fields.Many2one('module.overview', string="Module Overview", ondelete="cascade")
    name = fields.Char(string="Name")
    view_ids = fields.One2many('module.overview.model.view', 'model_id', string="Views")
    view_count = fields.Integer(string="View Count", compute="_compute_view_count")
    access_ids = fields.One2many('module.overview.model.access', 'model_id', string="Access Rules")
    access_count = fields.Integer(string="Access Count", compute="_compute_access_count")

    @api.one
    @api.depends('view_ids')
    def _compute_view_count(self):
        self.view_count = len(self.view_ids)

    @api.one
    @api.depends('access_ids')
    def _compute_access_count(self):
        self.access_count = len(self.access_ids)

class ModuleOverviewModelAccess(models.Model):

    _name = "module.overview.model.access"
    _description = "Module Overview Model Access"

    model_id = fields.Many2one('module.overview.model', string="Model", ondelete="cascade")
    name = fields.Char(string="Group Name")
    x_id = fields.Char(string="XML ID")
    perm_read = fields.Boolean(string="Read Permmision")
    perm_write = fields.Boolean(string="Write Permmision")
    perm_create = fields.Boolean(string="Create Permmision")
    perm_unlink = fields.Boolean(string="Delete Permmision")   
    access_string = fields.Char(string="Access String", compute="_compute_access_string")

    @api.one
    @api.depends('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
    def _compute_access_string(self):
        a_string = ""

        if self.perm_read:
            a_string += "Read, "

        if self.perm_write:
            a_string += "Write, "

        if self.perm_create:
            a_string += "Create, "

        if self.perm_unlink:
            a_string += "Delete, "

        self.access_string = a_string[:-2] 

class ModuleOverviewModelView(models.Model):

    _name = "module.overview.model.view"
    _description = "Module Overview Model View"

    model_id = fields.Many2one('module.overview.model', string="Model", ondelete="cascade")
    name = fields.Char(string="Name")
    x_id = fields.Char(string="XML ID")