# -*- coding: utf-8 -*-

import argparse
import sys
import requests
import json
import datetime
import base64
import logging
_logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except:
    _logger.error("Selenium not installed")

from odoo.http import request
from odoo import api, fields, models
from odoo.tools.translate import _

class SEMSettings(models.Model):

    _name = "sem.settings"
    _inherit = 'res.config.settings'

    def _default_tracking_code(self):
        return "<script async src=\"" + request.httprequest.host_url + "sem/tracking.js\"></script>\n<script>window.tracking_url = '" + request.httprequest.host_url + "sem/track';</script>"

    google_cse_key = fields.Char(string="Google CSE Key")
    google_search_engine_id = fields.Char(string="Google CSE Search Engine ID")
    google_ads_developer_token = fields.Char(string="Google Ads Developer Token")
    google_ads_client_id = fields.Char(string="Google Ads Client ID")
    google_ads_client_secret = fields.Char(string="Google Ads Client Secret")
    google_ads_manager_account_customer_id = fields.Char(string="Google Ads Manager Account Customer ID")
    google_my_business_client_id = fields.Char(string="Google My Business Client ID")
    google_my_business_client_secret = fields.Char(string="Google My Business Client Secret")
    bing_web_search_api_key = fields.Char(string="Bing Web Search v7 API Key")
    bing_maps_api_key = fields.Char(string="Bing Maps API Key")
    google_maps_api_key = fields.Char(string="Google Maps API Key")
    tracking_code = fields.Text(string="Tracking Code", default=_default_tracking_code)

    def test_google_maps_geocode(self):
        google_maps_api_key = self.env['ir.default'].get('sem.settings', 'google_maps_api_key')
        request_response = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key=" + google_maps_api_key)
        _logger.error(request_response.text)
        request_response_json = json.loads(request_response.text)

    @api.multi
    def google_ads_authorize(self):
        self.ensure_one()

        return_url = request.httprequest.host_url + "web"
        url = self.env['google.service']._get_authorize_uri(return_url, 'ads', scope='https://www.googleapis.com/auth/adwords')
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    @api.multi
    def google_my_business_authorize(self):
        self.ensure_one()

        return_url = request.httprequest.host_url + "web"
        url = self.env['google.service']._get_authorize_uri(return_url, 'business', scope='https://www.googleapis.com/auth/business.manage')
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

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
    def set_values(self):
        super(SEMSettings, self).set_values()
        self.env['ir.default'].set('sem.settings', 'google_cse_key', self.google_cse_key)
        self.env['ir.default'].set('sem.settings', 'google_search_engine_id', self.google_search_engine_id)
        self.env['ir.default'].set('sem.settings', 'google_ads_developer_token', self.google_ads_developer_token)
        self.env['ir.config_parameter'].set_param('google_ads_client_id', self.google_ads_client_id)
        self.env['ir.config_parameter'].set_param('google_ads_client_secret', self.google_ads_client_secret)
        self.env['ir.default'].set('sem.settings', 'google_ads_manager_account_customer_id', self.google_ads_manager_account_customer_id)
        self.env['ir.default'].set('sem.settings', 'bing_web_search_api_key', self.bing_web_search_api_key)
        self.env['ir.default'].set('sem.settings', 'bing_maps_api_key', self.bing_maps_api_key)
        self.env['ir.config_parameter'].set_param('google_business_client_id', self.google_my_business_client_id)
        self.env['ir.config_parameter'].set_param('google_business_client_secret', self.google_my_business_client_secret)
        self.env['ir.default'].set('sem.settings', 'google_maps_api_key', self.google_maps_api_key)

    @api.model
    def get_values(self):
        res = super(SEMSettings, self).get_values()
        res.update(
            google_cse_key=self.env['ir.default'].get('sem.settings', 'google_cse_key'),
            google_search_engine_id=self.env['ir.default'].get('sem.settings', 'google_search_engine_id'),
            google_ads_developer_token=self.env['ir.default'].get('sem.settings', 'google_ads_developer_token'),
            google_ads_client_id=self.env['ir.config_parameter'].get_param('google_ads_client_id'),
            google_ads_client_secret=self.env['ir.config_parameter'].get_param('google_ads_client_secret'),
            google_ads_manager_account_customer_id=self.env['ir.default'].get('sem.settings', 'google_ads_manager_account_customer_id'),
            bing_web_search_api_key=self.env['ir.default'].get('sem.settings', 'bing_web_search_api_key'),
            bing_maps_api_key=self.env['ir.default'].get('sem.settings', 'bing_maps_api_key'),
            google_my_business_client_id=self.env['ir.config_parameter'].get_param('google_business_client_id'),
            google_my_business_client_secret=self.env['ir.config_parameter'].get_param('google_business_client_secret'),
            google_maps_api_key=self.env['ir.default'].get('sem.settings', 'google_maps_api_key')
        )
        return res