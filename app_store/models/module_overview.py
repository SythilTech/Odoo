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
    private_access_ids = fields.Many2many('module.access', string="Private Access")
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

class ModuleAccess(models.Model):

    _name = "module.access"
    _description = "Module Access"

    name = fields.Char(string="Name")
    access_token = fields.Char(string="Access Token")
    module_access_ids = fields.Many2many('module.overview', tring="Module Access", help="Inactive modules this token allows access too")

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