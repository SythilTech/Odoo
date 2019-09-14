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

class SemTools(models.TransientModel):

    _name = "sem.tools"

    @api.model
    def check_url(self, url):

        webpage_report = self.env['sem.report.website.page'].create({'url': url})

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(chrome_options = chrome_options)
            driver.get(url)
            parsed_html = html.fromstring(driver.page_source)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            _logger.error(e)
            _logger.error("Line: " + str(exc_tb.tb_lineno) )
            # Fall back to requests and skip some checks that need Selenium / Google Chrome
            driver = False
            parsed_html = html.fromstring(requests.get(url).text)

        for seo_metric in self.env['sem.metric'].search([('active', '=', True)]):
            method = '_seo_metric_%s' % (seo_metric.function_name,)
            action = getattr(seo_metric, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            try:
                start = time.time()
                metric_result = action(driver, url, parsed_html)
                end = time.time()
                diff = end - start
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(seo_metric.name)
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if metric_result != False:
                self.env['sem.report.website.metric'].create({'website_report_page_id': webpage_report.id, 'metric_id': seo_metric.id, 'value': metric_result, 'time': diff})

        for seo_check in self.env['sem.check'].search([('active', '=', True), ('check_level', '=', 'page')]):
            method = '_seo_check_%s' % (seo_check.function_name,)
            action = getattr(seo_check, method, None)

            if not action:
                raise NotImplementedError('Method %r is not implemented' % (method,))

            try:
                start = time.time()
                check_result = action(driver, url, parsed_html)
                end = time.time()
                diff = end - start
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                _logger.error(seo_check.name)
                _logger.error(e)
                _logger.error("Line: " + str(exc_tb.tb_lineno) )
                continue

            if check_result != False:
                self.env['sem.report.website.check'].create({'website_report_page_id': webpage_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1], 'time': diff})

        try:
            driver.quit()
        except:
            pass

        return webpage_report