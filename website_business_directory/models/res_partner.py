# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerDirectory(models.Model):

    _inherit = "res.partner"

    #def _default_listing_level(self):
    #    return self.env['ir.model.data'].get_object('website_business_directory', 'free_listing')

    in_directory = fields.Boolean(string="In Directory")
    company_category_ids = fields.Many2many('res.partner.directory.category', string="Directory Categories")
    directory_description = fields.Text(string="Directory Description", translate=True)
    business_owner = fields.Many2one('res.users', string="Business Owner")
    city_id = fields.Many2one('res.country.state.city', string="City")
    latitude = fields.Char(String="Latitude")
    longitude = fields.Char(string="Longitude")
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
    directory_listing_open_hours = fields.One2many('website.directory.timeslot', 'business_id', string="Open Times")
    allow_restaurant_booking = fields.Boolean(string="Allow Restaurant Booking")
    display_online_menu = fields.Boolean(string="Display Online Menu")
    menu = fields.One2many('res.partner.directory.department', 'restaurant_id', string="Menu")
    directory_review_ids = fields.One2many('res.partner.directory.review', 'business_id', string=" Reviews")
    featured_listing = fields.Boolean(string="Featured Listing")
    listing_level = fields.Many2one('website.directory.level', string="Listing Level")
    
class WebsiteDirectoryTimeslot(models.Model):

    _name = "website.directory.timeslot"

    business_id = fields.Many2one('res.partner', string="Business")
    day = fields.Selection([('monday','Monday'), ('tuesday','Tuesday'), ('wednesday','Wednesday'), ('thursday','Thursday'), ('friday','Friday'), ('saturday','Saturday'), ('sunday','Sunday')], string="Day")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="End Time")

class WebsiteDirectoryBillingPlan(models.Model):

    _name = "website.directory.billingplan"

    name = fields.Char(string="Plan Name", required=True)
    frequency = fields.Selection([('MONTH','Monthly')], required=True, default="MONTH", string="Monthly")
    amount = fields.Float(string="Amount", required=True)
    
class WebsiteDirectoryReview(models.Model):

    _name = "res.partner.directory.review"

    business_id = fields.Many2one('res.partner', string="Business")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    rating = fields.Selection([('1','1 Star'), ('2','2 Star'), ('3','3 Star'), ('4','4 Star'), ('5','5 Star')], string="Rating")

class WebsiteDirectoryDepartment(models.Model):

    _name = "res.partner.directory.department"

    restaurant_id = fields.Many2one('res.partner', string="Restaurant")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    menu_item_ids = fields.One2many('res.partner.directory.department.menuitem', 'department_id', string="Menu Items")

class WebsiteDirectoryDepartmentMenuItem(models.Model):

    _name = "res.partner.directory.department.menuitem"

    department_id = fields.Many2one('res.partner.directory.department', string="Department")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    single_price = fields.Float(string="Price")

class WebsiteDirectoryCategory(models.Model):

    _name = "res.partner.directory.category"

    parent_category = fields.Many2one('res.partner.directory.category', string="Parent Category")
    children_category_ids = fields.One2many('res.partner.directory.category', 'parent_category', string="Child Categories")
    name = fields.Char(string="Category Name")