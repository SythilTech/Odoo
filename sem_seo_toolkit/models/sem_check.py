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

class SemCheck(models.Model):

    _name = "sem.check"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(string="Name")
    function_name = fields.Char(string="Function Name")
    description = fields.Text(string="Description")
    category_id = fields.Many2one('sem.check.category', string="Category")
    active = fields.Boolean(string="Active")
    keyword_required = fields.Boolean(string="Keyword Required")
    check_type = fields.Selection([('onsite', 'On Site'), ('offsite', 'Off Site')], string="Check Type", help="Offsite require search engine API intergration and can cost money")
    check_level = fields.Selection([('domain', 'Domain'), ('page', 'Page')], string="Check Level", help="Domain means only executes once\nPage is every page run the check")

    def _seo_check_keyword_in_title(self, request_response, parsed_html, keyword):

        title_tags = parsed_html.xpath("//title")

        if len(title_tags) == 0:
            #Fail 1: No title tag
            return (False, _("No title tag detected"))

        if len(title_tags) > 1:
            #Fail 2: More then one title tag
            return (False, _("Multiple title tags detected"))
 
        if len(title_tags) == 1:
            title_tag = title_tags[0]
            if keyword.lower() in title_tag.text.lower():
                #Pass 1: Keyword is substring of title
                return (True, "")
            else:
                #Fail 3: More then one title tag
                return (False, _("Keyword not in title \"%s\"") % title_tag.text)

    def _seo_check_title_exists(self, request_response, parsed_html, keyword):

        title_tags = parsed_html.xpath("//title")

        if len(title_tags) == 0:
            #Fail 1: No title tag
            return (False, _("No title tag detected"))

        if len(title_tags) > 1:
            #Fail 2: More then one title tag
            return (False, _("Multiple title tags detected"))
 
        if len(title_tags) == 1:
            #Pass 1: Only 1 title tag
            if len(title_tags[0].text) > 0:
                return (True, "")
            else:
                #Fail 3: Title tag is empty
                return (False, _("Title tag is empty"))

    def _seo_check_has_meta_description(self, request_response, parsed_html, keyword):

        meta_descriptions = parsed_html.xpath("//meta[@name='description']")

        if len(meta_descriptions) == 0:
            #Fail 1: No meta description
            return (False, _("No Meta description detected"))

        if len(meta_descriptions) > 1:
            #Fail 2: More then one meta description
            return (False, _("Multiple Meta descriptions detected"))
 
        if len(meta_descriptions) == 1:
            #Pass 1: Only 1 meta description
            if len(meta_descriptions[0].attrib['content']) > 0:
                return (True, "")
            else:
                #Fail 3: Meta description is empty
                return (False, _("Empty Meta description"))

    def _seo_check_valid_links(self, request_response, parsed_html, keyword):
        anchor_tags = parsed_html.xpath("//a")

        #Pass 1: Page has atleast 1 link that returns http 200
        check_pass = True
        check_notes = ""

        if len(anchor_tags) == 0:
            #Fail 1: No links on page, signs the page has no navigation
            return (False, _("No Links found on page"))

        for anchor_tag in anchor_tags:
            # Placeholder hyperlinks still count as valid
            if 'href' in anchor_tag.attrib:
                anchor_url_absolute = urljoin(request_response.url, anchor_tag.attrib['href'])

                try:
                    link_request_response = requests.head(anchor_url_absolute)

                    # Redirects are still a fail as it requires extra time to fetch the other page
                    if link_request_response.status_code != 200:
                        #Fail 2: Link returns status code other then http 200
                        check_pass = False
                        check_notes += "(" + str(link_request_response.status_code) + ") " + anchor_url_absolute + "<br/>"
                except:
                    #Fail 3: Assume it is 404 if requests can not connect
                    check_pass = False
                    check_notes += "(404) " + anchor_url_absolute + "<br/>"

        return (check_pass, check_notes)

    def _seo_check_valid_images(self, request_response, parsed_html, keyword):
        img_tags = parsed_html.xpath("//img")

        #Pass 1: Page has no images or all images return http 200
        check_pass = True
        check_notes = ""

        for img_tag in img_tags:
            if 'src' in img_tag.attrib:
                img_url_absolute = urljoin(request_response.url, img_tag.attrib['src'])

                try:
                    img_request_response = requests.head(anchor_url_absolute)

                    # Redirects are still a fail as it requires extra time to fetch the other page
                    if img_request_response.status_code != 200:
                        #Fail 2: Image returns status code other then http 200
                        check_pass = False
                        check_notes += "(" + str(img_request_response.status_code) + ") " + img_url_absolute + "<br/>"
                except:
                    #Fail 3: Assume it is 404 if requests can not connect
                    check_pass = False
                    check_notes += "(404) " + img_url_absolute + "<br/>"
            else:
                #Fail 4: Images with no src are invalid
                check_pass = False
                check_notes += _("Image has no src attribute") + "<br/>" + cgi.escape(html.tostring(img_tag).decode()) + "<br/>"

        return (check_pass, check_notes)

    def _seo_check_images_have_alt(self, request_response, parsed_html, keyword):
        img_tags = parsed_html.xpath("//img")
        
        #Pass 1: Page has no images or all images have a non empty alt tag
        check_pass = True
        check_notes = ""

        for img_tag in img_tags:
            if 'alt' in img_tag.attrib:
                if img_tag.attrib['alt'] == "":
                    #Fail 1: Any image has an empty alt attribute
                    check_pass = False
                    check_notes += _("Empty alt tag") + "<br/>" + cgi.escape(html.tostring(img_tag).decode()) + "<br/>"
            else:
                #Fail 2: Any image does not have alt attribute
                check_pass = False
                check_notes += _("Missing alt tag") + "<br/>" + cgi.escape(html.tostring(img_tag).decode()) + "<br/>"

        return (check_pass, check_notes)

    def _seo_check_page_load_time(self, request_response, parsed_html, keyword):

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options = chrome_options)
        driver.get(request_response.url)

        navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
        #response_start = driver.execute_script("return window.performance.timing.responseStart")
        dom_complete = driver.execute_script("return window.performance.timing.domComplete")

        driver.quit()

        navigation_start_datetime = datetime.datetime.fromtimestamp(navigation_start/1000)
        dom_complete_datetime = datetime.datetime.fromtimestamp(dom_complete/1000)

        dom_content_loaded = round((dom_complete_datetime - navigation_start_datetime).total_seconds(), 2)

        if dom_content_loaded <= 2.0:
            return (True, _("%s seconds") % dom_content_loaded)
        else:
            return (False, _("%s seconds") % dom_content_loaded)

    def _seo_check_non_optimised_images(self, request_response, parsed_html, keyword):

        check_pass = True
        check_notes = ""

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options = chrome_options)
        driver.get(request_response.url)

        images = driver.find_elements_by_tag_name('img')
        for image in images:
            display_width = image.value_of_css_property('width')
            display_height = image.value_of_css_property('width')

            img_url_absolute = urljoin(request_response.url, image.get_attribute('src'))
            
            data = requests.get(img_url_absolute).content
            im = Image.open(BytesIO(data))
            natural_width, natural_height = im.size

            # I can really only use pixel comparasion
            if "px" in display_width and "px" in display_height:
                if int(display_width[:-2]) != natural_width or int(display_height[:-2]) != natural_height:
                    check_pass = False
                    check_notes += img_url_absolute + "<br/>Display: " + str(display_width[:-2]) + "x" + str(display_height[:-2]) + "px, Natural: " + str(natural_width) + "x" + str(natural_height) + "px<br/>"

        driver.quit()

        return (check_pass, check_notes)

    def _seo_check_https(self, request_response, parsed_html, keyword):
        if request_response.url.startswith("https://"):
            #Pass 1: URL starts with https:// valid ceritifcate and mixed content are different checks
            return (True, "")
        else:
            #Fail 1: URL does not start with https:// assume http:// but is still invalid if someone checks an ftp site...
            return (False, "")

    def _seo_check_mixed_content(self, request_response, parsed_html, keyword):
        #Pass 1: page has no images / links OR URL is http:// OR URL is https:// and all images / links use https://
        check_pass = True
        check_notes = ""

        if request_response.url.startswith("https://"):
            # Check all image tags
            image_tags = parsed_html.xpath("//img")
            for image_tag in image_tags:
                if 'src' in image_tag.attrib:
                    if image_tag.attrib['src'].startswith("http://"):
                        check_pass = False
                        check_notes += _("Mixed Content \"%s\"") % image_tag.attrib['src'] + "<br/>"

            # Check all link tags
            link_tags = parsed_html.xpath("//a")
            for link_tag in link_tags:
                if 'href' in link_tag.attrib:
                    if link_tag.attrib['href'].startswith("http://"):
                        check_pass = False
                        check_notes += _("Mixed Content \"%s\"") % link_tag.attrib['href'] + "<br/>"

        return (check_pass, check_notes)

    def _seo_check_sitemap_exists(self, request_response, parsed_html, keyword):

        parsed_uri = urlparse(request_response.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

        try:
            sitemap_request_response = requests.get(domain + "sitemap.xml")
            #Pass 1: File sitemap.xml
            return (True, "")
        except:
            pass

        try:
            sitemap_request_response = requests.get(domain + "sitemap_index.xml")
            #Pass 2: File sitemap_index.xml exists
            return (True, "")
        except:
            pass

        #Fail 1: Neither sitemap.xml or sitemap_index.xml exist
        return (False, "")

    def _seo_check_index_allowed(self, request_response, parsed_html, keyword):

        meta_robots_indexes = parsed_html.xpath("//meta[@name='robots']")

        for meta_robots_index in meta_robots_indexes:
            if 'noindex' in meta_robots_index.attrib['content']:
                #Fail 1: Generic robots noindex
                return (False, _("robots meta noindex detected"))

        meta_googlebot_indexes = parsed_html.xpath("//meta[@name='googlebot']")

        for meta_googlebot_index in meta_googlebot_indexes:
            if 'noindex' in meta_googlebot_index.attrib['content']:
                #Fail 2: googlebot specific noindex
                return (False, _("googlebot meta noindex detected"))

        #TODO Fail 3: http header X-Robots-Tag

        #Pass 1: No noindex has been detected
        return (True, "")

    def _seo_check_google_domain_indexed(self, request_response, parsed_html, keyword):

        key = self.env['ir.default'].get('sem.settings', 'google_cse_key')
        cx = self.env['ir.default'].get('sem.settings', 'google_search_engine_id')

        # Skip the test if Google CSE is not setup
        if key is None or cx is None:
            return False

        parsed_uri = urlparse(request_response.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        index_request_response = requests.get("https://www.googleapis.com/customsearch/v1?key=" + key + "&cx=" + cx + "&q=site:" + domain)

        json_data = json.loads(index_request_response.text)

        search_results = json_data['queries']['request'][0]['totalResults']
        if int(search_results) > 0:
            #Pass 1: Atleast one page has been indexed by Google
            return (True, _("Google Index Rough Estimate %s") % search_results)

        #Fail 1: Returns 0 results
        return (False, "")

    def _seo_check_google_analytics(self, request_response, parsed_html, keyword):

        check_pass = False
        check_notes = ""

        if "google-analytics.com/ga.js" in request_response.text:
            check_pass = True
            check_notes += _("Google Analytics Detected") + "<br/>"

        if "stats.g.doubleclick.net/dc.js" in request_response.text:
            check_pass = True
            check_notes += _("Google Analytics Remarketing Detected") + "<br/>"

        if "google-analytics.com/analytics.js" in request_response.text:
            check_pass = True
            check_notes += _("Google Universal Analytics Detected") + "<br/>"

        if "googletagmanager.com/gtag/js" in request_response.text:
            check_pass = True
            check_notes += _("Google Analytics Global Site Tag Detected") + "<br/>"

        if "google-analytics.com/ga_exp.js" in request_response.text:
            check_pass = True
            check_notes += _("Google Analytics Experiments Detected") + "<br/>"

        if "googletagmanager.com/gtm.js" in request_response.text:
            # Might not have anaytics installed but count it anyway
            check_pass = True
            check_notes += _("Google Tag Manager Detected") + "<br/>"

        return (check_pass, check_notes)


    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('sem.check')
        values['sequence']=sequence
        return super(SemCheck, self).create(values)