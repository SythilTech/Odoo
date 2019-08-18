# -*- coding: utf-8 -*-
import sys
import requests
from lxml import html
import json
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SemClient(models.Model):

    _name = "sem.client"

    name = fields.Char(related="partner_id.name", string="Name")
    partner_id = fields.Many2one('res.partner', string="Contact")
    website_ids = fields.One2many('sem.client.website', 'client_id', string="Websites")

class SemClientWebsite(models.Model):

    _name = "sem.client.website"
    _rec_name = "url"

    client_id = fields.Many2one('sem.client', string="Client")
    url = fields.Char(string="URL")
    page_ids = fields.One2many('sem.client.website.page', 'website_id', string="Web Pages")
    keyword_ids = fields.One2many('sem.client.website.keyword', 'website_id', string="Keywords")

    @api.multi
    def check_website(self):
        self.ensure_one()

        try:
            request_response = requests.get(self.url)
        except:
            raise UserError(_("Error accessing website"))

        sem_report = self.env['sem.report.seo'].create({'client_id': self.client_id.id, 'url': self.url})

        # Domain level checks
        for seo_check in self.env['sem.check'].search([('active', '=', True), ('keyword_required', '=', False), ('check_level', '=', 'domain')]):
            method = '_seo_check_%s' % (seo_check.function_name,)
            action = getattr(seo_check, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            parsed_html = html.fromstring(request_response.text)

            try:
                check_result = action(request_response, parsed_html, False)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue
            
            if check_result != False:
                self.env['sem.report.seo.check'].create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1]})

        # Page level checks
        for seo_check in self.env['sem.check'].search([('active', '=', True), ('keyword_required', '=', False), ('check_level', '=', 'page')]):
            method = '_seo_check_%s' % (seo_check.function_name,)
            action = getattr(seo_check, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            parsed_html = html.fromstring(request_response.text)

            check_result = action(request_response, parsed_html, False)

            if check_result != False:
                self.env['sem.report.seo.check'].create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1]})

        return {
            'name': 'SEM Seo Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report',
            'type': 'ir.actions.act_window',
            'res_id': sem_report.id
        }

    @api.multi
    def competitor_analyse(self):
        self.ensure_one()

        competitor_report = self.env['sem.report.competition'].create({'client_id': self.client_id.id})

        for keyword in self.keyword_ids:
            for search_engine in self.env['sem.search_engine'].search([]):
                for search_result in search_engine.get_listings(keyword.name):
                    self.env['sem.report.competition.ranking'].create({'competition_id': competitor_report.id, 'engine_id': search_engine.id, 'locale': 'GLOBAL', 'keyword': keyword.name, 'position': search_result['position'], 'title': search_result['title'], 'link': search_result['link'], 'snippet': search_result['snippet']})

        return {
            'name': 'SEM Competition Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.competition',
            'type': 'ir.actions.act_window',
            'res_id': competitor_report.id
        }

    @api.multi
    def search_report(self):
        self.ensure_one()

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

        search_report = self.env['sem.report.search'].create({'website_id': self.id})

        for keyword in self.keyword_ids:
            if keyword.active:
                for geo_target in keyword.geo_target_ids:

                    payload = json.dumps({
                        "language": language,
                        "geo_target_constants":
                        [
                            "geoTargetConstants/" + geo_target.location_id
                        ],
                        "keyword_plan_network": keyword_plan_network,
                        "keyword_seed":
                        {
                            "keywords":
                            [
                                keyword.name
                            ]
                        }
                    })

                    response_string = requests.post("https://googleads.googleapis.com/v2/customers/" + manager_customer_id + ":generateKeywordIdeas", data=payload, headers=headers)

                    response_string_json = json.loads(response_string.text)

                    monthly_searches = "-"
                    competition = "-"

                    if "results" in response_string_json:
                        exact_match = response_string_json['results'][0]
                        if exact_match['text'] == keyword.name.lower():
                            monthly_searches = exact_match['keywordIdeaMetrics']['avgMonthlySearches']
                            if 'competition' in exact_match['keywordIdeaMetrics']:
                                competition = exact_match['keywordIdeaMetrics']['competition']

                    self.env['sem.report.search.result'].create({'search_id': search_report.id, 'keyword_id': keyword.id, 'geo_target_id': geo_target.id, 'monthly_searches': monthly_searches, 'competition': competition})

        return {
            'name': 'Search Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.search',
            'res_id': search_report.id,
            'type': 'ir.actions.act_window'
        } 

class SemClientWebsitePage(models.Model):

    _name = "sem.client.website.page"

    website_id = fields.Many2one('sem.client.website', string="Website")
    url = fields.Char(string="URL")

class SemClientWebsiteKeyword(models.Model):

    _name = "sem.client.website.keyword"

    website_id = fields.Many2one('sem.client.website', string="Website")
    name = fields.Char(string="Keyword")
    active = fields.Boolean(string="Active", default="True", help="Keywords can not be deleted only archived so new reports don't show them")
    geo_target_ids = fields.Many2many('sem.geo_target', string="Geo Targets")

    def find_geo_targets(self):
        self.ensure_one()

        return {
            'name': 'Find Geo Targets',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.geo_target.wizard',
            'target': 'new',
            'context': {'default_keyword_id': self.id},
            'type': 'ir.actions.act_window'
        } 