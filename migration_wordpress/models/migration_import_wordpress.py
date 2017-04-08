# -*- coding: utf-8 -*-
import requests
import logging
_logger = logging.getLogger(__name__)
import json
from openerp import api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
from lxml import html, etree
from openerp.http import request


class MigrationImportWordpress(models.Model):

    _name = "migration.import.wordpress"

    wordpress_url = fields.Char(string="Wordpress URL")    
    wordpress_page_ids = fields.One2many('migration.import.wordpress.page', 'wordpress_id', string="Wordpress Pages")
    wordpress_imported_media = fields.Many2many('ir.attachment', string="Imported Media")

    def transfer_media(self, media_json):
        """ Media can be imported from many palce such as when importing pages, media library, blog posts or posts of any type """
        url = media_json['guid']['rendered'].replace("localhost","10.0.0.68")

        filename = media_json['media_details']['sizes']['full']['file']
        
        external_identifier = "import_media_" + str(media_json['id'])

        #Create an external ID so we don't reimport the same media again
        media_attachment = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
        if media_attachment:
            #For now we don't reimport media to conserve bandwidth and speed up reimports
            _logger.error("Media already exists")        
        else:
            #Download the image and creat a public attachment
            image_data = base64.b64encode( requests.get(url).content )
            media_attachment = self.env['ir.attachment'].create({'name':filename, 'type':'binary', 'datas':image_data, 'datas_fname': filename, 'res_model': 'ir.ui.view', 'public': True})        

            #We need to keep track of any imported media
            self.wordpress_imported_media = [(4,media_attachment.id)]

            self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'ir.attachment', 'res_id': media_attachment.id })        

        return media_attachment
    
    def transform_post_content(self, content):
        """ Changes Wordpress content of any post type(page, blog, custom) to better fit in with the Odoo CMS, includes localising hyperlinks and media """

        #Also get media since we will be importing the images in the post
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/media")
        media_json_data = json.loads(response_string.text)

        root = html.fromstring(content)
        image_tags = root.xpath("//img")
	if len(image_tags) != 0:
	    for image_tag in image_tags:

                #Get the full size image by looping through all media until you find the one with this url
                for media_json in media_json_data:
                    for key, value in media_json['media_details']['sizes'].iteritems():
                        if value['source_url'] == image_tag.attrib['src']:
                            media_attachment = self.transfer_media(media_json)
                                
	        image_tag.attrib['src'] = "/web/image2/" + str(media_attachment.id) + "/" + image_tag.attrib['width'] + "x" + image_tag.attrib['height'] + "/" + str(media_attachment.name)

                #Reimplement image resposiveness the Odoo way
	        image_tag.attrib['class'] = "img-responsive " + image_tag.attrib['class']
	            
                #This gets moved into the src
	        image_tag.attrib.pop("width")
	        image_tag.attrib.pop("height")
	            
                #We only import the original image, not all size variants so this is meaningless
	        image_tag.attrib.pop("srcset")
	        image_tag.attrib.pop("sizes")
            
        #Modify anchor tags and map pages to the new url
        anchor_tags = root.xpath("//a")
	if len(anchor_tags) != 0:
	    for anchor_tag in anchor_tags:
	        #Only modify local links
	        if self.wordpress_url in anchor_tag.attrib['href']:
	            page_slug = anchor_tag.attrib['href'].split("/")[-2]
	            anchor_tag.attrib['href'] = "/page/" + page_slug
           
        transformed_content = etree.tostring(root, pretty_print=True)
        
        return transformed_content
    
    def import_media(self):
        
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/media")
        json_data = json.loads(response_string.text)
            
        for media_json in json_data:
            self.transfer_media(media_json)
  
    def import_pages(self):

        #Get Pages
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/pages")
        page_json_data = json.loads(response_string.text)
        
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

            transformed_content = "<?xml version=\"1.0\"?>\n" + self.transform_post_content(wraped_content)

            external_identifier = "import_post_" + str(page_json['id'])

            #Create an external ID so we don't reimport the same page again
            page_view = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
            if page_view:
                #If the page has already been all we do is update it
                page_view.arch_base = transformed_content
            else:
                new_page = self.env['ir.ui.view'].create({'name':slug, 'key':'website.' + slug, 'type': 'qweb', 'arch_base': transformed_content})
                self.env['migration.import.wordpress.page'].create({'wordpress_id': self.id, 'name': title, 'view_id': new_page.id, 'url': request.httprequest.host_url + 'page/' + slug})

                self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'ir.ui.view', 'res_id': new_page.id })
            
class MigrationImportWordpressPage(models.Model):

    _name = "migration.import.wordpress.page"

    wordpress_id = fields.Many2one('migration.import.wordpress', string="Wordpress Import")
    name = fields.Char(string="Name")
    view_id = fields.Many2one('ir.ui.view', string="View")
    url = fields.Char(string="URL")
