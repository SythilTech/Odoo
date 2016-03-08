# -*- coding: utf-8 -*
import os
from os import walk
import glob
from lxml import html, etree
import csv
import fnmatch
import zipfile
import logging
import StringIO
import ast
import base64
_logger = logging.getLogger(__name__)

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
    module_view_count = fields.Char(string="Module View Count", help="The amount of times the page for this module has been viewed")
    module_download_count = fields.Char(string="Module Download Count", help="The amount of times this module has been downloaded")
    module_name = fields.Char(string="Module Name")
    icon = fields.Binary(string="Icon")

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
                self.analyse_module(dir)
            
    def analyse_module(self, module_name):
        home_directory = os.path.expanduser('~')
        app_directory = home_directory + "/apps"
        
        #Read __openerp__.py file    
        with open(app_directory + "/" + module_name + "/__openerp__.py", 'r') as myfile:
            data = myfile.read().replace('\n', '')
            op_settings = ast.literal_eval(data)
        
        #Convert icon file to base64
        icon_base64 = ""
        if os.path.isfile(app_directory + "/" + module_name + "/static/description/icon.png"):
            with open(app_directory + "/" + module_name + "/static/description/icon.png", "rb") as image_file:
                icon_base64 = base64.b64encode(image_file.read())
    
        module_overview = self.env['module.overview'].create({'name': module_name, 'module_name': op_settings['name'], 'icon': icon_base64})
        
        for root, dirnames, filenames in os.walk(app_directory + '/' + module_name):
            for filename in fnmatch.filter(filenames, '*.xml'):            
                self._read_xml(open( os.path.join(root, filename) ).read(), module_overview.id)

            for filename in fnmatch.filter(filenames, '*.csv'):
                self._read_csv(filename, open( os.path.join(root, filename) ).read(), module_overview.id)

        #Create a zip of the module (TODO include dependacies)
        zf = zipfile.ZipFile(app_directory + "/" + module_name + ".zip", "w")
	for dirname, subdirs, files in os.walk(app_directory + "/" + module_name):
	    zf.write(dirname)
	    for filename in files:
	        zf.write(os.path.join(dirname, filename))
        zf.close()

    def _read_csv(self, file_name, file_content, m_id):
        if "ir.model.access":
            rownum = 0
            reader = csv.reader(StringIO.StringIO(file_content), delimiter=',')
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
       
    def _read_xml(self, file_content, m_id):
        return_string = ""
        root = etree.fromstring(file_content)
        
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
    