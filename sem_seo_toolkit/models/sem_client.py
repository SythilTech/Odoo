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

    # TODO move this somewhere more meaningfull as the listing might not even have a website and 1 Google account can have multiple SEM clients on it
    @api.multi
    def google_my_business_report(self):
        self.ensure_one()

        if self.env['google.business'].need_authorize():
            raise UserError(_("Need to authorize with Google My Business first"))

        #Get a new access token
        refresh_token = self.env['ir.config_parameter'].get_param('google_business_refresh_token')
        all_token = self.env['google.service']._refresh_google_token_json(refresh_token, 'business')
        access_token = all_token.get('access_token')

        headers = {'Authorization': 'Bearer ' + access_token}
        account_response = requests.get("https://mybusiness.googleapis.com/v4/accounts", headers=headers)
        account_response_json = json.loads(account_response.text)
        google_search_engine = self.env['ir.model.data'].get_object('sem_seo_toolkit','seo_search_engine_google')
        end_date = datetime.datetime.utcnow()
        start_date = datetime.datetime.now() - datetime.timedelta(30)

        for account in account_response_json['accounts']:
            account_name = account['name']
            location_response = requests.get("https://mybusiness.googleapis.com/v4/" + account_name + "/locations", headers=headers)
            location_response_json = json.loads(location_response.text)

            # Just add all locations to a list so we can feed them all into the one reportInsights call
            locations = []
            for location in location_response_json['locations']:
                locations.append(location['name'])

                # Create or find a local listing entry so we can track performance since last report
                local_listing_search = self.env['sem.client.listing'].search([('search_engine_id','=', google_search_engine.id), ('listing_external_id','=', location['name'])])
                if len(local_listing_search) == 0:
                    local_listing = self.env['sem.client.listing'].create({'search_engine_id': google_search_engine.id, 'name': location['locationName'], 'listing_external_id': location['name']})
                else:
                    local_listing = local_listing_search[0]

                location_report = self.env['sem.report.google.business'].create({'listing_id': local_listing.id, 'start_date': start_date, 'end_date': end_date})

                media_response = requests.get("https://mybusiness.googleapis.com/v4/" + location['name'] + "/media", headers=headers)
                media_response_json = json.loads(media_response.text)
                
                if 'mediaItems' in media_response_json:
                    for media_item in media_response_json['mediaItems']:

                        # Create or find a local copy of the media so we can use it in the report
                        local_media_search = self.env['sem.client.listing.media'].search([('media_external_id','=', media_item['name'])])
                        if len(local_media_search) == 0:
                            google_thumbnail_image = base64.b64encode( requests.get(media_item['thumbnailUrl']).content )
                            local_media = self.env['sem.client.listing.media'].create({'listing_id': local_listing.id, 'image': google_thumbnail_image, 'media_external_id': media_item['name']})
                        else:
                            local_media = local_media_search[0]

                        if 'viewCount' in media_item['insights']:
                            self.env['sem.report.google.business.media'].create({'report_id': location_report.id, 'media_id': local_media.id, 'view_count': media_item['insights']['viewCount']})

        # All metrics within last 30 days
        # TODO feed 10 locations in at a time as that is the limit (https://developers.google.com/my-business/reference/rest/v4/accounts.locations/reportInsights)
        zulu_current_time = end_date.isoformat('T') + "Z"
        zulu_past = start_date.isoformat('T') + "Z"
        payload = json.dumps({
            "locationNames": locations,
            "basicRequest": {
                "metricRequests": [
                    {
                        "metric": "ALL"
                    }
                ],
                "timeRange": {
                    "startTime": zulu_past,
                    "endTime": zulu_current_time
                }
            }
        })

        # Since the metric information is done in bulk we update the records as we needed the report already created for the media metrics
        insight_response = requests.post("https://mybusiness.googleapis.com/v4/" + account_name + "/locations:reportInsights", data=payload, headers=headers)
        insight_response_json = json.loads(insight_response.text)
        for location_insight in insight_response_json['locationMetrics']:
            location_report = self.env['sem.report.google.business'].search([('listing_id.listing_external_id', '=', location_insight['locationName'])])
            update_vals = {}
            for metric_value in location_insight['metricValues']:
                # Don't include the AGGREGATED_TOTAL
                if 'metric' in metric_value:
                    update_vals[metric_value['metric'].lower()] = metric_value['totalValue']['value']

            location_report.update(update_vals)

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