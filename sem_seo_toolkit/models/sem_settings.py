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

    google_cse_key = fields.Char(string="Google CSE Key")
    google_search_engine_id = fields.Char(string="Google CSE Search Engine ID")
    google_ads_developer_token = fields.Char(string="Google Ads Developer Token")
    google_ads_client_id = fields.Char(string="Google Ads Client ID")
    google_ads_client_secret = fields.Char(string="Google Ads Client Secret")
    google_ads_manager_account_customer_id = fields.Char(string="Google Ads Manager Account Customer ID")

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

    @api.model
    def get_values(self):
        res = super(SEMSettings, self).get_values()
        res.update(
            google_cse_key=self.env['ir.default'].get('sem.settings', 'google_cse_key'),
            google_search_engine_id=self.env['ir.default'].get('sem.settings', 'google_search_engine_id'),
            google_ads_developer_token=self.env['ir.default'].get('sem.settings', 'google_ads_developer_token'),
            google_ads_client_id=self.env['ir.config_parameter'].get_param('google_ads_client_id'),
            google_ads_client_secret=self.env['ir.config_parameter'].get_param('google_ads_client_secret'),
            google_ads_manager_account_customer_id=self.env['ir.default'].get('sem.settings', 'google_ads_manager_account_customer_id')
        )
        return res