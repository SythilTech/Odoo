# -*- coding: utf-8 -*-

import argparse
import sys
import requests
import json
import logging
_logger = logging.getLogger(__name__)

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
    bing_web_search_api_key = fields.Char(string="Bing Web Search v7 API Key")
    tracking_code = fields.Text(string="Tracking Code", default=_default_tracking_code)

    def test_bing_search(self):
        headers = {'Ocp-Apim-Subscription-Key': self.bing_web_search_api_key}
        keyword = "Test Keyword"
        response = requests.get("https://api.cognitive.microsoft.com/bing/v7.0/search?q=" + keyword, headers=headers)
        _logger.error(response.text)
        response_json = json.loads(response.text)
        for webpage in response_json['webPages']['value']:
            _logger.error(webpage['name'])
            _logger.error(webpage['url'])
            _logger.error(webpage['snippet'])

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
            bing_web_search_api_key=self.env['ir.default'].get('sem.settings', 'bing_web_search_api_key')
        )
        return res