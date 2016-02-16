# -*- coding: utf-8 -*
from openerp import api, fields, models

class ModuleOverview(models.Model):

    _name = "module.overview"
    
    name = fields.Char(string="Module Name")
    models_ids = fields.One2many('module.overview.model', 'mo_id', string="Models")
    menu_ids = fields.One2many('module.overview.menu', 'mo_id', string="Menus")

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
    
    