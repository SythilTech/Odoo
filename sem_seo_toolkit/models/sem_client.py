# -*- coding: utf-8 -*-
import sys
import requests
from lxml import html
import json
import datetime
from urllib.parse import urljoin, urlparse
import base64
import time
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except:
    _logger.error("Selenium not installed")

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SemClient(models.Model):

    _name = "sem.client"

    name = fields.Char(related="partner_id.name", string="Name")
    partner_id = fields.Many2one('res.partner', string="Contact")
    website_ids = fields.One2many('sem.client.website', 'client_id', string="Websites")
    website_count = fields.Integer(compute='_compute_website_count', string="Website Count")

    @api.depends('website_ids')
    def _compute_website_count(self):
        for seo_client in self:
            seo_client.website_count = len(seo_client.website_ids)

class SemClientWebsite(models.Model):

    _name = "sem.client.website"
    _rec_name = "url"

    client_id = fields.Many2one('sem.client', string="Client")
    url = fields.Char(string="URL")
    page_ids = fields.One2many('sem.client.website.page', 'website_id', string="Web Pages")
    page_count = fields.Integer(compute='_compute_page_count', string="Page Count")
    search_context_ids = fields.Many2many('sem.search.context', string="Search Contexts")

    @api.depends('page_ids')
    def _compute_page_count(self):
        for webpage in self:
            webpage.page_count = len(webpage.page_ids)

    def read_sitemap(self):

        parsed_uri = urlparse(self.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

        sitemap_index_request_response = requests.get(domain + "sitemap_index.xml")
        sitemap_index_root = etree.fromstring(sitemap_index_request_response.text.encode("utf-8"))

        # TODO deal better with namespaces and sitemaps that have the loc not in the first position
        for sitemap in sitemap_index_root:
            sitemap_url = sitemap[0].text

            sitemap_request_response = requests.get(sitemap_url)
            sitemap_root = etree.fromstring(sitemap_request_response.text.encode("utf-8"))
            
            # Add to the websites page list if the url is not already there
            for sitemap_url_parent in sitemap_root:
                sitemap_url = sitemap_url_parent[0].text
                if self.env['sem.client.website.page'].search_count([('website_id','=',self.id), ('url','=',sitemap_url)]) == 0:
                    self.env['sem.client.website.page'].create({'website_id': self.id, 'url': sitemap_url})

    @api.multi
    def check_website(self):
        self.ensure_one()

        sem_website_report = self.env['sem.report.website'].create({'website_id': self.id})

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(chrome_options = chrome_options)
            driver.get(self.url)
            parsed_html = html.fromstring(driver.page_source)
        except:
            # Fall back to requests and skip some checks that need Selenium / Google Chrome
            driver = False
            parsed_html = html.fromstring(requests.get(self.url).text)

        for seo_check in self.env['sem.check'].search([('active', '=', True), ('check_level', '=', 'domain')]):
            method = '_seo_check_%s' % (seo_check.function_name,)
            action = getattr(seo_check, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            try:
                start = time.time()
                check_result = action(driver, self.url, parsed_html)
                end = time.time()
                diff = end - start
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(seo_check.name)
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if check_result != False:
                self.env['sem.report.website.check'].create({'website_report_id': sem_website_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        try:
            driver.quit()
        except:
            pass

        # Run page level checks then attach them to this report as children so we can create one massive pdf with each page
        for page in self.page_ids:
            if page.active:
                sem_report = page.check_webpage()
                sem_report.website_report_id = sem_website_report.id

        return {
            'name': 'Website Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.website',
            'type': 'ir.actions.act_window',
            'res_id': sem_website_report.id
        }

    @api.multi
    def ranking_report(self):
        self.ensure_one()

        ranking_report = self.env['sem.report.ranking'].create({'website_id': self.id})

        for search_context in self.search_context_ids:
            search_results = search_context.get_search_results()

            rank = "-"
            url = ""
            # Quick way of finding url that starts with the domain
            found_result = self.env['sem.search.results.result'].search([('results_id','=', search_results.id), ('url','=like', self.url + '%')], limit=1)
            if found_result:
                rank = found_result.position
                url = found_result.url

            self.env['sem.report.ranking.result'].create({'ranking_id': ranking_report.id, 'search_context_id': search_context.id, 'search_result_id': found_result.id or False, 'rank': rank, 'url': url})

        return {
            'name': 'Ranking Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.ranking',
            'res_id': ranking_report.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def search_report(self):
        self.ensure_one()

        search_report = self.env['sem.report.search'].create({'website_id': self.id})

        for search_context in self.search_context_ids:
            search_insight = search_context.get_insight()
            search_insight['search_id'] = search_report.id
            search_insight['search_context_id'] = search_context.id
            self.env['sem.report.search.result'].create(search_insight)

        return {
            'name': 'Search Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.search',
            'res_id': search_report.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def add_search_context(self):
        self.ensure_one()

        return {
            'name': 'Create Search Context',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.search.context.wizard',
            'target': 'new',
            'context': {'default_type': 'search', 'default_website_id': self.id},
            'type': 'ir.actions.act_window'
        }