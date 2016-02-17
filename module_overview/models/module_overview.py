# -*- coding: utf-8 -*
from openerp import api, fields, models

class ModuleOverview(models.Model):

    _name = "module.overview"
    
    name = fields.Char(string="Module Name")
    models_ids = fields.One2many('module.overview.model', 'mo_id', string="Models")
    menu_ids = fields.One2many('module.overview.menu', 'mo_id', string="Menus")
    access_ids = fields.One2many('module.overview.access', 'mo_id', string="Access Rules")
    model_count = fields.Integer(string="Model Count", compute="_compute_model_count")

    @api.one
    @api.depends('models_ids')
    def _compute_model_count(self):
        self.model_count = len(self.models_ids)
    
class ModuleOverviewAccess(models.Model):

    _name = "module.overview.access"
    
    mo_id = fields.Many2one('module.overview', string="Module Overview")
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
    
    mo_id = fields.Many2one('module.overview', string="Module Overview")
    name = fields.Char(string="Name")
    x_id = fields.Char(string="XML ID")
    parent = fields.Char(string="Parent Menu")
    
class ModuleOverviewModel(models.Model):

    _name = "module.overview.model"
    
    mo_id = fields.Many2one('module.overview', string="Module Overview")
    name = fields.Char(string="Name")
    view_ids = fields.One2many('module.overview.model.view', 'model_id', string="Views")
    
class ModuleOverviewModelView(models.Model):

    _name = "module.overview.model.view"
    
    model_id = fields.Many2one('module.overview.model', string="Model")
    name = fields.Char(string="Name")
    x_id = fields.Char(string="XML ID")
    
    