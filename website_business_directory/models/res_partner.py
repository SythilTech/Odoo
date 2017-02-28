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
    directory_review_ids = fields.One2many('res.partner.directory.review', 'business_id', string=" Reviews")
    directory_images = fields.One2many('website.directory.image', 'listing_id', string="Images")
    directory_listing_open_hours = fields.One2many('website.directory.timeslot', 'business_id', string="Open Times")
    directory_listing_monday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=','0')], string="Monday Open Times")
    directory_listing_tuesday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',1)], string="Tuesday Open Times")
    directory_listing_wednesday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',2)], string="Wednesday Open Times")
    directory_listing_thursday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',3)], string="Thursday Open Times")
    directory_listing_friday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',4)], string="Friday Open Times")
    directory_listing_saturday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',5)], string="Saturday Open Times")
    directory_listing_sunday_open_hours = fields.One2many('website.directory.timeslot', 'business_id', domain=[('day','=',6)], string="Sunday Open Times")
    
class WebsiteDirectoryTimeslot(models.Model):

    _name = "website.directory.timeslot"

    business_id = fields.Many2one('res.partner', string="Business")
    day = fields.Selection([('0','Monday'), ('1','Tuesday'), ('2','Wednesday'), ('3','Thursday'), ('4','Friday'), ('5','Saturday'), ('6','Sunday')], string="Day")
    start_time = fields.Float(string="Start Time")
    start_time_string = fields.Char(compute='_compute_start_time_string', store=True, string="Start Time String")
    end_time = fields.Float(string="End Time")
    end_time_string = fields.Char(compute='_compute_end_time_string', store=True, string="End Time String")

    @api.one
    @api.depends('start_time')
    def _compute_start_time_string(self):
        self.start_time_string = '%02d:%02d' % divmod(self.start_time * 60, 60)

    @api.one    
    @api.depends('end_time')
    def _compute_end_time_string(self):
        self.end_time_string = '%02d:%02d' % divmod(self.end_time * 60, 60)
    
class ResPartnerDirectoryReview(models.Model):

    _name = "res.partner.directory.review"

    business_id = fields.Many2one('res.partner', string="Business")
    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    rating = fields.Selection([('1','1 Star'), ('2','2 Star'), ('3','3 Star'), ('4','4 Star'), ('5','5 Star')], string="Rating")

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
    listing_ids = fields.Many2many('res.partner', string="Listings")
    name = fields.Char(string="Category Name")