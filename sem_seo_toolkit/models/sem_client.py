# -*- coding: utf-8 -*-
import sys
import requests
from lxml import html
import json
import urllib.parse as urlparse
import base64
import time
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

class SemClientWebsite(models.Model):

    _name = "sem.client.website"
    _rec_name = "url"

    client_id = fields.Many2one('sem.client', string="Client")
    url = fields.Char(string="URL")
    page_ids = fields.One2many('sem.client.website.page', 'website_id', string="Web Pages")
    keyword_ids = fields.One2many('sem.client.website.keyword', 'website_id', string="Keywords")

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
    def check_website(self):
        self.ensure_one()

        sem_report = self.env['sem.report.seo'].create({'client_id': self.client_id.id, 'url': self.url})

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

        # Domain level checks
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
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if check_result != False:
                self.env['sem.report.seo.check'].create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        # Page level checks
        for seo_check in self.env['sem.check'].search([('active', '=', True), ('check_level', '=', 'page')]):
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
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if check_result != False:
                self.env['sem.report.seo.check'].create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        try:
            driver.quit()
        except:
            pass

        return {
            'name': 'SEM Seo Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.seo',
            'type': 'ir.actions.act_window',
            'res_id': sem_report.id
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
    def ranking_report(self):
        self.ensure_one()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options = chrome_options)

        ranking_report = self.env['sem.report.ranking'].create({'website_id': self.id})

        for keyword in self.keyword_ids:
            if keyword.active:
                for geo_target in keyword.geo_target_ids:

                    url = "https://www.google.com/search?tbs=cdr%3A1%2Ccd_min%3A1%2F1%2F2000&q="
                    url += keyword.name.lower()
                    url += "&num=100&ip=0.0.0.0&source_ip=0.0.0.0&ie=UTF-8&oe=UTF-8&hl=en&adtest=on&noj=1&igu=1"

                    key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

                    uule = "w+CAIQICI"
                    uule += key[len(geo_target.name) % len(key)]
                    uule += base64.b64encode(bytes(geo_target.name, "utf-8")).decode()
                    url += "&uule=" + uule
                    url += "&adtest-useragent=" + geo_target.device_id.user_agent

                    driver.implicitly_wait(2)
                    driver.get(url)
                    organic_counter = 1
                    rank = 0
                    link_url = ""

                    organic_hook = '//*[@class="srg"]/*[@data-hveid]'

                    for organic_listing in driver.find_elements(By.XPATH, organic_hook):

                        try:

                            heading = organic_listing.find_element(By.XPATH, './/a//*[@role="heading"]')
                            index_date = organic_listing.find_element(By.XPATH, './/*[@class="f"]')
                            url_anchor = organic_listing.find_element(By.XPATH, './/a[@ping]')
                            parsed = urlparse.urlparse(url_anchor.get_attribute('ping'))
                            link_url = urlparse.parse_qs(parsed.query)['url'][0]

                            if link_url.startswith(self.url):
                                rank = organic_counter
                                break

                            organic_counter += 1
                        except:
                            pass

                    # Create the ranking even if the client's website is not found
                    self.env['sem.report.ranking.result'].create({'ranking_id': ranking_report.id, 'keyword_id': keyword.id, 'geo_target_id': geo_target.id, 'rank': rank, 'search_url': url, 'link_url': link_url, 'search_html': driver.page_source})

        driver.quit()

        return {
            'name': 'Ranking Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.ranking',
            'res_id': ranking_report.id,
            'type': 'ir.actions.act_window'
        }

class SemClientWebsitePage(models.Model):

    _name = "sem.client.website.page"

    website_id = fields.Many2one('sem.client.website', string="Website")
    url = fields.Char(string="URL")

class SemClientWebsiteKeyword(models.Model):

    _name = "sem.client.website.keyword"

    website_id = fields.Many2one('sem.client.website', string="Website")
    name = fields.Char(string="Keyword")
    active = fields.Boolean(string="Active", default="True", help="Keywords can not be deleted only archived so new reports don't show them")
    geo_target_ids = fields.Many2many('sem.geo_target', string="Geo Targets")

    def find_geo_targets(self):
        self.ensure_one()

        return {
            'name': 'Find Geo Targets',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.geo_target.wizard',
            'target': 'new',
            'context': {'default_keyword_id': self.id},
            'type': 'ir.actions.act_window'
        } 