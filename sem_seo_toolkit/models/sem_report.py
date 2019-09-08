# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemReportWebsite(models.Model):

    _name = "sem.report.website"

    website_id = fields.Many2one('sem.client.website', string="Website")
    check_ids = fields.One2many('sem.report.website.check', 'website_report_id', string="Domain Level Checks")
    page_ids = fields.One2many('sem.report.website.page', 'website_report_id', string="Pages")

class SemReportWebsitePage(models.Model):

    _name = "sem.report.website.page"

    website_report_id = fields.Many2one('sem.report.website', string="Report Website")
    page_id = fields.Many2one('sem.client.website.page', string="Page")
    url = fields.Char(string="URL")
    check_ids = fields.One2many('sem.report.website.check', 'website_report_page_id', string="Page Level Checks")
    metric_ids = fields.One2many('sem.report.website.metric', 'website_report_page_id', string="Page Level Metrics")

class SemReportWebsiteCheck(models.Model):

    _name = "sem.report.website.check"

    website_report_id = fields.Many2one('sem.report.website', string="Website Report")
    website_report_page_id = fields.Many2one('sem.report.website.page', string="Page Report")
    check_id = fields.Many2one('sem.check', string="SEO Check")
    check_pass = fields.Boolean(string="Pass", help="Did it pass or fail this check/test")
    notes = fields.Html(sanitize=False, string="Notes", help="Any additional information")
    time = fields.Float(string="Processing Time")

class SemReportWebsiteMetric(models.Model):

    _name = "sem.report.website.metric"

    website_report_page_id = fields.Many2one('sem.report.website.page', string="Page Report")
    metric_id = fields.Many2one('sem.metric', string="Metric")
    value = fields.Char(string="Value")
    time = fields.Float(string="Processing Time")

class SemReportSearch(models.Model):

    _name = "sem.report.search"

    website_id = fields.Many2one('sem.client.website', string="Client Website")
    result_ids = fields.One2many('sem.report.search.result', 'search_id', string="Results")

class SemReportSearchResult(models.Model):

    _name = "sem.report.search.result"

    search_id = fields.Many2one('sem.report.search', string="Search Report")
    search_context_id = fields.Many2one('sem.search.context', string="Search Context")
    monthly_searches = fields.Char(string="Monthly Searches")
    competition = fields.Char(string="Competition")

class SemReportGoogleBusiness(models.Model):

    _name = "sem.report.google.business"

    listing_id = fields.Many2one('sem.client.listing', string="Listing")
    start_date = fields.Date(string="Report Start Period")
    end_date = fields.Date(string="Report End Period")
    media_ids = fields.One2many('sem.report.google.business.media', 'report_id')
    queries_direct = fields.Integer(string="Queries Direct")
    queries_indirect = fields.Integer(string="Queries Indirect")
    queries_chain = fields.Integer(string="Queries Chain")
    views_maps = fields.Integer(string="Views Maps")
    views_search = fields.Integer(string="Views Search")
    actions_website = fields.Integer(string="Actions Website")
    actions_phone = fields.Integer(string="Actions Phone")
    actions_driving_directions = fields.Integer(string="Actions Driving Directions")
    photos_views_merchant = fields.Integer(string="Photos Views Merchant")
    photos_views_customers = fields.Integer(string="Photos Views Customers")
    photos_count_merchant = fields.Integer(string="Photos Count Merchant")
    photos_count_customers = fields.Integer(string="Photos Count Customers")
    local_post_views_search = fields.Integer(string="Local Post Views Search")
    local_post_actions_call_to_action = fields.Integer(string="Local Post Actions Call to Action")

class SemReportGoogleBusinessMedia(models.Model):

    _name = "sem.report.google.business.media"

    report_id = fields.Many2one('sem.report.google.business', string="GMB Report")
    media_id = fields.Many2one('sem.client.listing.media', string="Media")
    image = fields.Binary(related="media_id.image", string="Image")
    view_count = fields.Integer(string="View Count")