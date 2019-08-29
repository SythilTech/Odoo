# -*- coding: utf-8 -*-

import argparse
import sys
import requests
import json
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
    #google_my_business_client_id = fields.Char(string="Google My Business Client ID")
    #google_my_business_client_secret = fields.Char(string="Google My Business Client Secret")
    bing_web_search_api_key = fields.Char(string="Bing Web Search v7 API Key")
    bing_maps_api_key = fields.Char(string="Bing maps API Key")
    tracking_code = fields.Text(string="Tracking Code", default=_default_tracking_code)

    def test_google_my_business(self):
         # Have to wait for access before I can start feature...
        response = requests.get("https://mybusiness.googleapis.com/v4/accounts")
        _logger.error(response.text)

        #All metrics within last 30 days
        payload = json.dumps({
            "locationNames": [
                "accounts/account_name/locations/locationId"
            ],
            "basicRequest": {
                "metricRequests": [
                    {
                        "metric": "ALL"
                    }
                ],
                "timeRange": {
                    "startTime": "2016-10-12T01:01:23.045123456Z",
                    "endTime": "2017-01-10T23:59:59.045123456Z"
                }
            }
        })

        response = requests.post("https://mybusiness.googleapis.com/v4/{name=accounts/*}/locations:reportInsights", data=payload)
        _logger.error(response.text)
        response_json = json.loads(response.text)
        create_vals = {}
        create_vals['queries_direct'] = response_json['QUERIES_DIRECT']
        create_vals['queries_indirect'] = response_json['QUERIES_INDIRECT']
        create_vals['queries_chain'] = response_json['QUERIES_CHAIN']
        create_vals['views_maps'] = response_json['VIEWS_MAPS']
        create_vals['views_search'] = response_json['VIEWS_SEARCH']
        create_vals['actions_website'] = response_json['ACTIONS_WEBSITE']
        create_vals['actions_phone'] = response_json['ACTIONS_PHONE']
        create_vals['actions_driving_directions'] = response_json['ACTIONS_DRIVING_DIRECTIONS']
        create_vals['photos_views_merchant'] = response_json['PHOTOS_VIEWS_MERCHANT']
        create_vals['photos_views_customers'] = response_json['PHOTOS_VIEWS_CUSTOMERS']
        create_vals['photos_count_merchant'] = response_json['PHOTOS_COUNT_MERCHANT']
        create_vals['photos_count_customers'] = response_json['PHOTOS_COUNT_CUSTOMERS']
        create_vals['local_post_views_search'] = response_json['LOCAL_POST_VIEWS_SEARCH']
        create_vals['local_post_actions_call_to_action'] = response_json['LOCAL_POST_ACTIONS_CALL_TO_ACTION']
        self.env['sem.report.google.business'].create(create_vals)

    @api.multi
    def google_ads_authorize(self):
        self.ensure_one()

        return_url = request.httprequest.host_url + "web"
        url = self.env['google.service']._get_authorize_uri(return_url, 'ads', scope='https://www.googleapis.com/auth/adwords')
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

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
            bing_maps_api_key=self.env['ir.default'].get('sem.settings', 'bing_maps_api_key')
        )
        return res