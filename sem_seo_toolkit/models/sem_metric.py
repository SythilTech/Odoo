# -*- coding: utf-8 -*-
import sys
from lxml import html
from lxml import etree
import cgi
import requests
from urllib.parse import urljoin, urlparse
import logging
_logger = logging.getLogger(__name__)
from PIL import Image
from io import BytesIO

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
except:
    _logger.error("Selenium not installed")

import json
import datetime
import urllib.request

from odoo import api, fields, models, _

class SemMetric(models.Model):

    _name = "sem.metric"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(string="Name")
    function_name = fields.Char(string="Function Name")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active")

    def _seo_metric_page_load_time(self, driver, url, parsed_html):

        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        dom_complete = driver.execute_script("return window.performance.timing.domComplete")

        navigation_start_datetime = datetime.datetime.fromtimestamp(navigation_start/1000)
        dom_complete_datetime = datetime.datetime.fromtimestamp(dom_complete/1000)

        return round((dom_complete_datetime - navigation_start_datetime).total_seconds(), 2)

    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('sem.metric')
        values['sequence']=sequence
        return super(SemMetric, self).create(values)