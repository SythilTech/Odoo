# -*- coding: utf-8 -*-

from odoo import api, fields, models

class GoogleAds(models.Model):

    _name = "google.ads"
    _description = "Google Ads"

    @api.model
    def set_all_tokens(self, authorization_code):
        all_token = self.env['google.service']._get_google_token_json(authorization_code, 'ads')
        self.env['ir.config_parameter'].set_param('google_ads_refresh_token', all_token.get('refresh_token') )
        self.env['ir.config_parameter'].set_param('google_ads_access_token', all_token.get('access_token') )

    @api.model
    def need_authorize(self):
        return self.env['ir.config_parameter'].get_param('google_ads_refresh_token') is False