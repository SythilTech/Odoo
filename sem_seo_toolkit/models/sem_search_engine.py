# -*- coding: utf-8 -*-

import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError
from odoo import api, fields, models, _

class SemSearchEngine(models.Model):

    _name = "sem.search.engine"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Function Name")

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
                geo_targets.append({'location_id': geo_target_constant['id'], 'name': geo_target_constant['canonicalName'].replace(",",", ")})

        return geo_targets

    def _find_geo_targets_bing(self, location_string):
        bing_api_key = self.env['ir.default'].get('sem.settings', 'bing_maps_api_key')
        request_response = requests.get("http://dev.virtualearth.net/REST/v1/Locations/" + location_string + "?key=" + bing_api_key)
        response_json = json.loads(request_response.text)
        geo_targets = []
        for resource_set in response_json['resourceSets']:
            for resource in resource_set['resources']:
                latitude = resource['point']['coordinates'][0]
                longitude = resource['point']['coordinates'][1]
                geo_targets.append({'latitude': latitude, 'longitude': longitude, 'name': resource['name'], 'accuracy_radius_meters': 22})

        return geo_targets

    def perform_search(self, search_context):
        method = '_perform_search_%s' % (self.internal_name,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented' % (method,))

        return action(search_context)

    def _perform_search_google(self, search_context):
        # As the Google CSE API doesn't allow very context sensitive results we instead provide a link
        # This link aids agents in manually entering search result information
        url = "https://www.google.com/search?q="
        url += search_context.keyword.lower()
        url += "&num=100&ip=0.0.0.0&source_ip=0.0.0.0&ie=UTF-8&oe=UTF-8&hl=en&adtest=on&noj=1&igu=1"

        key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

        uule = "w+CAIQICI"
        uule += key[len(search_context.geo_target_name) % len(key)]
        uule += base64.b64encode(bytes(search_context.geo_target_name, "utf-8")).decode()
        url += "&uule=" + uule
        url += "&adtest-useragent=" + search_context.device_id.user_agent 

        return {'search_url': url}

    def _perform_search_bing(self, search_context):
        bing_web_search_api_key = self.env['ir.default'].get('sem.settings', 'bing_web_search_api_key')
        headers = {'Ocp-Apim-Subscription-Key': bing_web_search_api_key, 'User-Agent': search_context.device_id.user_agent, 'X-Search-Location': "lat:" + search_context.latitude + ";long:" + search_context.longitude + ";re:" + search_context.accuracy_radius_meters}
        response = requests.get("https://api.cognitive.microsoft.com/bing/v7.0/search?q=" + search_context.keyword + "&count=50", headers=headers)
        response_json = json.loads(response.text)
        search_results = []

        position_counter = 0
        for webpage in response_json['webPages']['value']:
            position_counter += 1
            link_url = webpage['url'].replace("\\","")
            search_results.append( (0, 0,  {'position': position_counter, 'name': webpage['name'], 'url': link_url, 'snippet': webpage['snippet']}) )

        # Return the full results as well as ranking information if the site was found
        return {'raw_data': response.text, 'result_ids': search_results}
 
    def get_insight(self, search_context):
        method = '_get_insight_%s' % (self.internal_name,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented' % (method,))

        return action(search_context)

    def _get_insight_google(self, search_context):

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

        payload = json.dumps({
            "language": language,
            "geo_target_constants":
            [
                "geoTargetConstants/" + search_context.location_id
            ],
            "keyword_plan_network": keyword_plan_network,
            "keyword_seed":
            {
                "keywords":
                [
                    search_context.keyword
                ]
            }
        })

        response_string = requests.post("https://googleads.googleapis.com/v2/customers/" + manager_customer_id + ":generateKeywordIdeas", data=payload, headers=headers)

        response_string_json = json.loads(response_string.text)

        monthly_searches = "-"
        competition = "-"

        if "results" in response_string_json:
            exact_match = response_string_json['results'][0]
            if exact_match['text'] == search_context.keyword.lower():
                monthly_searches = exact_match['keywordIdeaMetrics']['avgMonthlySearches']
                if 'competition' in exact_match['keywordIdeaMetrics']:
                    competition = exact_match['keywordIdeaMetrics']['competition']

        return {'monthly_searches': monthly_searches, 'competition': competition}