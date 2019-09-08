# -*- coding: utf-8 -*-

from odoo import api, fields, models

class GoogleBusiness(models.Model):

    _name = "google.business"
    _description = "Google Business"

    @api.model
    def set_all_tokens(self, authorization_code):
        all_token = self.env['google.service']._get_google_token_json(authorization_code, 'business')
        self.env['ir.config_parameter'].set_param('google_business_refresh_token', all_token.get('refresh_token') )
        self.env['ir.config_parameter'].set_param('google_business_access_token', all_token.get('access_token') )

    @api.model
    def need_authorize(self):
        return self.env['ir.config_parameter'].get_param('google_business_refresh_token') is False