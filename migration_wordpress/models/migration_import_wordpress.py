# -*- coding: utf-8 -*-

import requests
import logging
_logger = logging.getLogger(__name__)
import json
import base64
from lxml import html, etree

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.http import request

class MigrationImportWordpress(models.Model):

    _name = "migration.import.wordpress"
    _rec_name = "wordpress_url"

    wordpress_url = fields.Char(string="Wordpress URL")    
    wordpress_page_ids = fields.One2many('website.page', 'wordpress_id', string="Wordpress Pages")
    wordpress_imported_media = fields.Many2many('ir.attachment', string="Imported Media")
    wordpress_imported_user_ids = fields.Many2many('res.users', string="Imported Users")

    def transfer_user(self, user_json):
        """ For now this is only used by the blog so we can credit the original author """

        external_identifier = "import_user_" + str(user_json['id'])

        #Create an external ID so we don't reimport the same user again
        wordpress_user = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
        if wordpress_user:
            #For now we don't reimport the users
            _logger.error("User already exists")
        else:
            #Since we don't seem to get the username, email or password from the API we just create a stub user
            wordpress_user = self.env['res.users'].create({'login': 'wordpress_' + str(user_json['id']), 'notify_email': 'none', 'email': 'wordpress_' + str(user_json['id']) + "@example.fake.au", 'name': user_json['name'], 'active':True})

            #We need to keep track of any imported users
            self.wordpress_imported_user_ids = [(4,wordpress_user.id)]

            self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'res.users', 'res_id': wordpress_user.id })

        return wordpress_user

    def transfer_media(self, media_json):
        """ Media can be imported from many places such as when importing pages, media library, blog posts or posts of any type """

        if 'code' in media_json:
            #Access denied so can not import image
            return False

        url = media_json['guid']['rendered']

        filename = url.split('/')[-1]
        
        external_identifier = "import_media_" + str(media_json['id'])

        #Create an external ID so we don't reimport the same media again
        media_attachment = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
        if media_attachment:
            #For now we don't reimport media to conserve bandwidth and speed up reimports
            media_attachment.name = filename
        else:
            #Download the image and creat a public attachment
            image_data = base64.b64encode( requests.get(url).content )
            media_attachment = self.env['ir.attachment'].create({'name':filename, 'type':'binary', 'datas':image_data, 'datas_fname': filename, 'res_model': 'ir.ui.view', 'public': True})

            #We need to keep track of any imported media
            self.wordpress_imported_media = [(4,media_attachment.id)]

            self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'ir.attachment', 'res_id': media_attachment.id })

        return media_attachment

    def pagination_requests(self, url):
        """Repeats the request multiple time until it has all pages"""

        response_string = requests.get(url + "?per_page=100&page=1")
        combined_json_data = json.loads(response_string.text)

        if "X-WP-TotalPages" in response_string.headers:
            total_pages = int(response_string.headers['X-WP-TotalPages'])

            if total_pages > 1:
                for page in range(2, total_pages + 1 ):
                    response_string = requests.get(url + "?per_page=100&page=" + str(page) )
                    combined_json_data = combined_json_data + json.loads(response_string.text)

        return combined_json_data

    def transform_post_content(self, content, media_json_data):
        """ Changes Wordpress content of any post type(page, blog, custom) to better fit in with the Odoo CMS, includes localising hyperlinks and media """

        root = html.fromstring(content)
        image_tags = root.xpath("//img")
        if len(image_tags) != 0:
            for image_tag in image_tags:

                media_attachment = False

                #Get the full size image by looping through all media until you find the one with this url
                for media_json in media_json_data:
                    if 'sizes' in media_json['media_details']:
                        for key, value in media_json['media_details']['sizes'].items():
                            if value['source_url'] == image_tag.attrib['src'] or value['source_url'] == image_tag.attrib['src'].replace("/",'\/'):
                                media_attachment = self.transfer_media(media_json)
                    else:
                        if media_json['guid']['rendered'] == image_tag.attrib['src'] or media_json['guid']['rendered'] == image_tag.attrib['src'].replace("/",'\/'):
                            media_attachment = self.transfer_media(media_json)

                if media_attachment:
                    if "width" in image_tag.attrib and "height" in image_tag.attrib:
                        image_tag.attrib['src'] = "/web/image2/" + str(media_attachment.id) + "/" + image_tag.attrib['width'] + "x" + image_tag.attrib['height'] + "/" + str(media_attachment.name)
                    else:
                        image_tag.attrib['src'] = "/web/image/" + str(media_attachment.id)

                #Reimplement image resposiveness the Odoo way
                if "class" in image_tag.attrib:
                    image_tag.attrib['class'] = "img-responsive " + image_tag.attrib['class']
                else:
                    image_tag.attrib['class'] = "img-responsive"

                #This gets moved into the src
                if "width" in image_tag.attrib:
                    image_tag.attrib.pop("width")

                if "height" in image_tag.attrib:
                    image_tag.attrib.pop("height")

                #We only import the original image, not all size variants so this is meaningless
                if "srcset" in image_tag.attrib:
                    image_tag.attrib.pop("srcset")

                if "sizes" in image_tag.attrib:
                    image_tag.attrib.pop("sizes")

        #Modify anchor tags and map pages to the new url
        anchor_tags = root.xpath("//a")
        if len(anchor_tags) != 0:
            for anchor_tag in anchor_tags:
                #Only modify local links
                if "href" in anchor_tag.attrib:
                    if self.wordpress_url in anchor_tag.attrib['href']:
                        page_slug = anchor_tag.attrib['href'].split("/")[-2]
                        anchor_tag.attrib['href'] = "/" + page_slug

        transformed_content = etree.tostring(root, encoding='unicode')

        return transformed_content

    def import_media(self):

        media_json_data = self.pagination_requests(self.wordpress_url + "/wp-json/wp/v2/media")

        for media_json in media_json_data:
            self.transfer_media(media_json)

    def import_pages(self):

        page_json_data = self.pagination_requests(self.wordpress_url + "/wp-json/wp/v2/pages")

        #Also get media since we will be importing the images in the post
        media_json_data = self.pagination_requests(self.wordpress_url + "/wp-json/wp/v2/media")

        for page_json in page_json_data:

            title = page_json['title']['rendered']
            slug = page_json['slug']
            content = page_json['content']['rendered']

            wraped_content = ""
            wraped_content += "<t t-name=\"website." + slug + "\">\n"
            wraped_content += "  <t t-call=\"website.layout\">\n"
            wraped_content += "    <div id=\"wrap\" class=\"oe_structure oe_empty\"/>\n"
            wraped_content += "    <div class=\"container\">\n"
            wraped_content += content
            wraped_content += "    </div>\n"
            wraped_content += "  </t>\n"
            wraped_content += "</t>"

            transformed_content = "<?xml version=\"1.0\"?>\n" + self.transform_post_content(wraped_content, media_json_data)
            external_identifier = "import_post_" + str(page_json['id'])

            #Create an external ID so we don't reimport the same page again
            page_view = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
            if page_view:
                #If the page has already been all we do is update it
                page_view.arch_base = transformed_content
            else:
            
                #Create the view first + external ID
                new_view = self.env['ir.ui.view'].create({'name':slug, 'key':'website.' + slug, 'type': 'qweb', 'arch': transformed_content})
                self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'ir.ui.view', 'res_id': new_view.id })

                #Now we create the page
                self.env['website.page'].create({'wordpress_id': self.id, 'name': title, 'view_id': new_view.id, 'url': '/' + slug})