# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerDirectory(models.Model):

    _inherit = "res.partner"

    in_directory = fields.Boolean(string="In Directory")
    company_category_ids = fields.Many2many('res.partner.directory.category', string="Directory Categories")
    directory_description = fields.Text(string="Directory Description")
    business_owner = fields.Many2one('res.users', string="Business Owner")
    directory_monday_start = fields.Float(string="Monday Start Time")
    directory_monday_end = fields.Float(string="Monday End Time")
    directory_tuesday_start = fields.Float(string="Tuesday Start Time")
    directory_tuesday_end = fields.Float(string="Tuesday End Time")
    directory_wednesday_start = fields.Float(string="Wednesday Start Time")
    directory_wednesday_end = fields.Float(string="Wednesday End Time")
    directory_thursday_start = fields.Float(string="Thursday Start Time")
    directory_thursday_end = fields.Float(string="Thursday End Time")
    directory_thursday_start = fields.Float(string="Saturday Start Time")
    directory_thursday_end = fields.Float(string="Saturday End Time")
    directory_friday_start = fields.Float(string="Friday Start Time")
    directory_friday_end = fields.Float(string="Friday End Time")
    directory_saturday_start = fields.Float(string="Saturday Start Time")
    directory_saturday_end = fields.Float(string="Saturday End Time")
    directory_sunday_start = fields.Float(string="Sunday Start Time")
    directory_sunday_end = fields.Float(string="Sunday End Time")
    allow_restaurant_booking = fields.Boolean(string="Allow Restaurant Booking")
    display_online_menu = fields.Boolean(string="Display Online Menu")
    menu = fields.One2many('res.partner.directory.department', 'restaurant_id', string="Menu")

class ResPartnerDirectoryDepartment(models.Model):

    _name = "res.partner.directory.department"

    restaurant_id = fields.Many2one('res.partner', string="Restaurant")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    menu_item_ids = fields.One2many('res.partner.directory.department.menuitem', 'department_id', string="Menu Items")

class ResPartnerDirectoryDepartmentMenuItem(models.Model):

    _name = "res.partner.directory.department.menuitem"

    department_id = fields.Many2one('res.partner.directory.department', string="Department")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    single_price = fields.Float(string="Price")

class ResPartnerDirectoryCategory(models.Model):

    _name = "res.partner.directory.category"

    parent_category = fields.Many2one('res.partner.directory.category', string="Parent Category")
    children_category_ids = fields.One2many('res.partner.directory.category', 'parent_category', string="Child Categories")
    name = fields.Char(string="Category Name")