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
                geo_targets.append({'location_id': geo_target_constant['id'], 'name': geo_target_constant['canonicalName']})

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

    def get_ranking(self, geo_target, domain, keyword):
        method = '_get_ranking_%s' % (self.internal_name,)
        action = getattr(self, method, None)

        if not action:
            raise NotImplementedError('Method %r is not implemented' % (method,))

        return action(geo_target, domain, keyword)

    def _get_ranking_google(self, geo_target, domain, keyword):
        # As the Google CSE API doesn't allow geo specific results more specific then country level instead we provide a link
        # This link aids agents in manually collecting ranking information
        # After a Google Search Console account is setup ranking information can be obtained from that???
        url = "https://www.google.com/search?q="
        url += keyword.name.lower()
        url += "&num=100&ip=0.0.0.0&source_ip=0.0.0.0&ie=UTF-8&oe=UTF-8&hl=en&adtest=on&noj=1&igu=1"

        key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

        uule = "w+CAIQICI"
        uule += key[len(geo_target.name) % len(key)]
        uule += base64.b64encode(bytes(geo_target.name, "utf-8")).decode()
        url += "&uule=" + uule
        url += "&adtest-useragent=" + geo_target.device_id.user_agent
        
        return {'search_url': url}

    def _get_ranking_bing(self, geo_target, domain, keyword):
        bing_web_search_api_key = self.env['ir.default'].get('sem.settings', 'bing_web_search_api_key')
        payload = {'count': 50}
        headers = {'Ocp-Apim-Subscription-Key': bing_web_search_api_key, 'User-Agent': geo_target.device_id.user_agent, 'X-Search-Location': "lat:" + geo_target.latitude + ";long:" + geo_target.longitude + ";re:" + str(geo_target.accuracy_radius_meters)}
        response = requests.get("https://api.cognitive.microsoft.com/bing/v7.0/search?q=" + keyword.name, data=payload, headers=headers)
        response_json = json.loads(response.text)
        rank_counter = 0
        search_results = []
        rank = False
        rank_link_url = False
        for webpage in response_json['webPages']['value']:
            rank_counter += 1
            link_url = webpage['url'].replace("\\","")
            search_results.append( (0, 0,  {'name': webpage['name'], 'url': link_url, 'snippet': webpage['snippet']}) )
            if link_url.startswith(domain):
                rank = rank_counter
                rank_link_url = link_url

        # Return the full results as well as ranking information if the site was found
        return {'rank': rank, 'link_url': rank_link_url, 'item_ids': search_results}