# -*- coding: utf-8 -*-
import sys
import requests
from lxml import html
import json
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
    keyword_ids = fields.One2many('sem.client.website.keyword', 'website_id', string="Keywords")
    keyword_count = fields.Integer(compute='_compute_keyword_count', string="Keyword Count")

    @api.depends('page_ids')
    def _compute_page_count(self):
        for webpage in self:
            webpage.page_count = len(webpage.page_ids)

    @api.depends('keyword_ids')
    def _compute_keyword_count(self):
        for webpage in self:
            webpage.keyword_count = len(webpage.keyword_ids)

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
    def metric_report(self):
        self.ensure_one()

        metric_report = self.env['sem.report.metric'].create({'url': self.url})

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

        for seo_metric in self.env['sem.metric'].search([('active', '=', True)]):
            method = '_seo_metric_%s' % (seo_metric.function_name,)
            action = getattr(seo_metric, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            try:
                metric_result = action(driver, self.url, parsed_html)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if metric_result != False:
                self.env['sem.report.metric.result'].create({'report_metric_id': metric_report.id, 'metric_id': seo_metric.id, 'value': metric_result})

        try:
            driver.quit()
        except:
            pass

        return {
            'name': 'SEM Metric Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.metric',
            'type': 'ir.actions.act_window',
            'res_id': metric_report.id
        }

    @api.multi
    def competitor_analyse(self):
        self.ensure_one()

        competitor_report = self.env['sem.report.competition'].create({'client_id': self.client_id.id})

        for keyword in self.keyword_ids:
            for search_engine in self.env['sem.search_engine'].search([]):
                for search_result in search_engine.get_listings(keyword.name):
                    self.env['sem.report.competition.ranking'].create({'competition_id': competitor_report.id, 'engine_id': search_engine.id, 'locale': 'GLOBAL', 'keyword': keyword.name, 'position': search_result['position'], 'title': search_result['title'], 'link': search_result['link'], 'snippet': search_result['snippet']})

        return {
            'name': 'SEM Competition Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.competition',
            'type': 'ir.actions.act_window',
            'res_id': competitor_report.id
        }

    @api.multi
    def check_website(self):
        self.ensure_one()

        sem_website_report = self.env['sem.report.seo.website'].create({'website_id': self.id})

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
                self.env['sem.report.seo.check'].create({'website_report_id': sem_website_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        try:
            driver.quit()
        except:
            pass

        # Run page level checks then attach them to this report as children so we can create one massive pdf with each page
        for page in self.page_ids:
            if page.active:
                sem_report = page.check_webpage()
                sem_report.report_website_id = sem_website_report.id

        return {
            'name': 'SEM Seo Website Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.seo.website',
            'type': 'ir.actions.act_window',
            'res_id': sem_website_report.id
        }

    @api.multi
    def search_report(self):
        self.ensure_one()

        if self.env['google.ads'].need_authorize():
            raise UserError(_("Need to authorize with Google Ads first"))

        #Get a new access token
        refresh_token = self.env['ir.config_parameter'].get_param('google_ads_refresh_token')
        all_token = self.env['google.service']._refresh_google_token_json(refresh_token, 'ads')
        access_token = all_token.get('access_token')

        manager_customer_id = self.env['ir.default'].get('sem.settings', 'google_ads_manager_account_customer_id').replace("-","")
        developer_token = self.env['ir.default'].get('sem.settings', 'google_ads_developer_token')
        headers = {'login-customer-id': manager_customer_id, 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token, 'developer-token': developer_token}

        # TODO allow for other languages
        language = 'languageConstants/1000' #English

        # TODO allow this to be configured
        keyword_plan_network = "GOOGLE_SEARCH"

        search_report = self.env['sem.report.search'].create({'website_id': self.id})

        for keyword in self.keyword_ids:
            if keyword.active:
                for geo_target in keyword.geo_target_ids:

                    payload = json.dumps({
                        "language": language,
                        "geo_target_constants":
                        [
                            "geoTargetConstants/" + geo_target.location_id
                        ],
                        "keyword_plan_network": keyword_plan_network,
                        "keyword_seed":
                        {
                            "keywords":
                            [
                                keyword.name
                            ]
                        }
                    })

                    response_string = requests.post("https://googleads.googleapis.com/v2/customers/" + manager_customer_id + ":generateKeywordIdeas", data=payload, headers=headers)

                    response_string_json = json.loads(response_string.text)

                    monthly_searches = "-"
                    competition = "-"

                    if "results" in response_string_json:
                        exact_match = response_string_json['results'][0]
                        if exact_match['text'] == keyword.name.lower():
                            monthly_searches = exact_match['keywordIdeaMetrics']['avgMonthlySearches']
                            if 'competition' in exact_match['keywordIdeaMetrics']:
                                competition = exact_match['keywordIdeaMetrics']['competition']

                    self.env['sem.report.search.result'].create({'search_id': search_report.id, 'keyword_id': keyword.id, 'geo_target_id': geo_target.id, 'monthly_searches': monthly_searches, 'competition': competition})

        return {
            'name': 'Search Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.search',
            'res_id': search_report.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def maps_report(self):
        self.ensure_one()

        for keyword in self.keyword_ids:
            if keyword.active:
                for geo_target in keyword.geo_target_ids:
                    zoom_level = str(geo_target.map_zoom_level)
                    url = "https://www.google.com/maps/search/" + keyword.name + "/@" + geo_target.latitude + "," + geo_target.lonhitude + "," + zoom_level + "z"

        return {
            'name': 'Maps Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.map',
            'res_id': maps_report.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def ranking_report(self):
        self.ensure_one()

        ranking_report = self.env['sem.report.ranking'].create({'website_id': self.id})

        for keyword in self.keyword_ids:
            if keyword.active:
                for geo_target in keyword.geo_target_ids:

                    create_dict = {'ranking_id': ranking_report.id, 'keyword_id': keyword.id, 'geo_target_id': geo_target.id}

                    # For Google this returns search_url, for Bing this returns rank, link_url and item_ids
                    create_dict.update(geo_target.get_ranking(self.url, keyword))

                    # Create the ranking entry even if the client's website is not found
                    self.env['sem.report.ranking.result'].create(create_dict)

        return {
            'name': 'Ranking Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.ranking',
            'res_id': ranking_report.id,
            'type': 'ir.actions.act_window'
        }

class SemClientWebsiteKeyword(models.Model):

    _name = "sem.client.website.keyword"

    website_id = fields.Many2one('sem.client.website', string="Website")
    name = fields.Char(string="Keyword")
    active = fields.Boolean(string="Active", default="True", help="Keywords can not be deleted only archived so new reports don't show them")
    geo_target_ids = fields.Many2many('sem.geo_target', string="Geo Targets")

    @api.multi
    def find_geo_targets(self):
        self.ensure_one()

        # Clean up list from previous searches
        for geo_result in self.env['sem.geo_target.wizard.record'].search([]):
            geo_result.unlink()

        return {
            'name': 'Find Geo Targets',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.geo_target.wizard',
            'target': 'new',
            'context': {'default_keyword_id': self.id},
            'type': 'ir.actions.act_window'
        } 