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
    google_my_business_client_id = fields.Char(string="Google My Business Client ID")
    google_my_business_client_secret = fields.Char(string="Google My Business Client Secret")
    bing_web_search_api_key = fields.Char(string="Bing Web Search v7 API Key")
    bing_maps_api_key = fields.Char(string="Bing Maps API Key")
    tracking_code = fields.Text(string="Tracking Code", default=_default_tracking_code)

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
            google_my_business_client_secret=self.env['ir.config_parameter'].get_param('google_business_client_secret')
        )
        return res