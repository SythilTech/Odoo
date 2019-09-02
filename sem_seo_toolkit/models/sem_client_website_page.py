# -*- coding: utf-8 -*-

import sys
import requests
from lxml import html
import time
import logging
_logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except:
    _logger.error("Selenium not installed")

from odoo import api, fields, models

class SemClientWebsitePage(models.Model):

    _name = "sem.client.website.page"
    _rec_name = "url"

    website_id = fields.Many2one('sem.client.website', string="Website")
    url = fields.Char(string="URL")
    active = fields.Boolean(string="Active", default=True)
    seo_report_ids = fields.One2many('sem.report.seo', 'page_id', string="SEO Reports")

    @api.onchange('website_id')
    def _onchange_website_id(self):
        if self.website_id.url:
            self.url = self.website_id.url

    @api.multi
    def check_webpage_wrapper(self):
        self.ensure_one()

        sem_report = self.check_webpage()

        return {
            'name': 'SEM Seo Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.seo',
            'type': 'ir.actions.act_window',
            'res_id': sem_report.id
        }

    @api.multi
    def check_webpage(self):
        self.ensure_one()

        sem_report = self.env['sem.report.seo'].create({'client_id': self.website_id.client_id.id, 'page_id': self.id, 'url': self.url})

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(chrome_options = chrome_options)
            driver.get(self.url)
            parsed_html = html.fromstring(driver.page_source)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error(e)
            _logger.error("Line: " + str(exc_tb.tb_lineno) )
            # Fall back to requests and skip some checks that need Selenium / Google Chrome
            driver = False
            parsed_html = html.fromstring(requests.get(self.url).text)

        for seo_check in self.env['sem.check'].search([('active', '=', True), ('check_level', '=', 'page')]):
            method = '_seo_check_%s' % (seo_check.function_name,)
            action = getattr(seo_check, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            try:
                start = time.time()
                check_result = action(driver, self.url, parsed_html)
                end = time.time()
                diff = end - start
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(seo_check.name)
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if check_result != False:
                self.env['sem.report.seo.check'].create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        try:
            driver.quit()
        except:
            pass

        return sem_report