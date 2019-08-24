# -*- coding: utf-8 -*-

import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError
from odoo import api, fields, models, _

class SemSearchEngine(models.Model):

    _name = "sem.search_engine"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Function Name")

    def get_listings(self, keyword):
        method = '_get_listings_%s' % (self.internal_name,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented' % (method,))

        return action(keyword)

    def _get_listings_google(self, keyword):

        key = self.env['ir.default'].get('sem.settings', 'google_cse_key')
        cx = self.env['ir.default'].get('sem.settings', 'google_search_engine_id')

        # Skip the test if Google CSE is not setup
        if key == False or cx == False:
            raise UserError(_("Google CSE not setup"))

        keyword_response = requests.get("https://www.googleapis.com/customsearch/v1?key=" + key + "&cx=" + cx + "&q=" + keyword)

        json_data = json.loads(keyword_response.text)

        search_results = []
        position_counter = 1
        for search_result in json_data['items']:
            search_results.append({'position': position_counter, 'title': search_result['title'], 'link': search_result['link'], 'snippet': search_result['snippet'], 'json_data': json_data})
            position_counter += 1

        return search_results

    def find_geo_targets(self, location_string):
        method = '_find_geo_targets_%s' % (self.internal_name,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented' % (method,))

        return action(location_string)    

    def _find_geo_targets_google(self, location_string):

        if self.env['google.ads'].need_authorize():
            raise UserError(_("Need to authorize with Google Ads first"))

        #Get a new access token
        refresh_token = self.env['ir.config_parameter'].get_param('google_ads_refresh_token')
        all_token = self.env['google.service']._refresh_google_token_json(refresh_token, 'ads')
        access_token = all_token.get('access_token')

        manager_customer_id = self.env['ir.default'].get('sem.settings', 'google_ads_manager_account_customer_id').replace("-","")
        developer_token = self.env['ir.default'].get('sem.settings', 'google_ads_developer_token')
        headers = {'login-customer-id': manager_customer_id, 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token, 'developer-token': developer_token}

        payload = json.dumps({
            "location_names": 
            {
                "names":
                [
                    location_string
                ]
            }
        })

        response_string = requests.post("https://googleads.googleapis.com/v2/geoTargetConstants:suggest", data=payload, headers=headers)

        response_string_json = json.loads(response_string.text)

        geo_targets = []

        if "geoTargetConstantSuggestions" in response_string_json:
            for geo_target_constant in response_string_json['geoTargetConstantSuggestions']:
                geo_target_constant = geo_target_constant['geoTargetConstant']
                geo_targets.append((geo_target_constant['id'], geo_target_constant['canonicalName']))

        return geo_targets