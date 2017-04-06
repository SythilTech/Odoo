# -*- coding: utf-8 -*-
import requests
import logging
_logger = logging.getLogger(__name__)
import json
from openerp import api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
from lxml import html, etree

class MigrationImportWordpress(models.Model):

    _name = "migration.import.wordpress"

    wordpress_url = fields.Char(string="Wordpress URL")    
    wordpress_page_ids = fields.One2many('migration.import.wordpress.page', 'wordpress_id', string="Wordpress Pages")
    
    @api.multi
    def import_content(self):
        self.ensure_one()
        for import_content in self.import_content_ids:
            method = '_import_%s' % (import_content.internal_name,)
	    action = getattr(self, method, None)
	    	        
	    if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	    action()
	    
        #return {
        #    'type': 'ir.actions.act_url',
        #    'target': 'self',
        #    'url': '/'
        #}

    def import_media(self):
        
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/media")
        json_data = json.loads(response_string.text)
            
        for media_json in json_data:
            url = media_json['guid']['rendered']
            filename = url.split("/")[-1]
            image_data = base64.b64encode( requests.get(url).content )
            
            #Don't import the same image twice
            if self.env['ir.attachment'].search_count([('name','=',filename)]) == 0:
                self.env['ir.attachment'].create({'name':filename, 'type':'binary', 'datas':image_data, 'datas_fname': filename, 'res_model': 'ir.ui.view', 'public': True})
  
    def import_pages(self):
        _logger.error("Import Pages")

        #Get Pages
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/pages")
        page_json_data = json.loads(response_string.text)

        #Also get media since we will be importing the images in the page
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/media")
        media_json_data = json.loads(response_string.text)
        
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

            root = etree.fromstring(wraped_content)
            image_tags = root.xpath("//img")
	    if len(image_tags) != 0:
	        for image_tag in image_tags:

                    #Get the full size image by looping through all media until the find the one with this url
                    for media_json in media_json_data:
                        for key, value in media_json['media_details']['sizes'].iteritems():
                            if value['source_url'] == image_tag.attrib['src']:
                                image_url = media_json['guid']['rendered'].replace("localhost","10.0.0.45")

                                image_slug = media_json['slug']
                                image_filename = image_url.split("/")[-1]
            
                                #Don't import the same image twice
                                attachment = self.env['ir.attachment'].search([('name','=',image_filename)])

                                if self.env['ir.attachment'].search_count([('name','=',image_filename)]) == 0:
                                    image_data = base64.b64encode( requests.get(image_url).content )
                                    attachment = self.env['ir.attachment'].create({'name':image_filename, 'type':'binary', 'datas':image_data, 'datas_fname': image_filename, 'res_model': 'ir.ui.view', 'public': True})                            
                        
	            image_tag.attrib['src'] = "/web/image2/" + str(attachment.id) + "/" + image_tag.attrib['width'] + "x" + image_tag.attrib['height'] + "/" + image_slug

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

            transformed_content = "<?xml version=\"1.0\"?>\n" + transformed_content
            
            page_view = self.env['ir.ui.view'].search([('key','=','website.' + slug)])
            if page_view:
                #Update the page
                page_view.arch_base = transformed_content
            else:
                #Create the view if it does not exist
                self.env['ir.ui.view'].create({'name':slug, 'key':'website.' + slug, 'type': 'qweb', 'arch_base': transformed_content})
                self.env['migration.import.wordpress.page'].create({'wordpress_id': self.id, 'name': title, 'url': '/page/' + slug})

class MigrationImportWordpressPage(models.Model):

    _name = "migration.import.wordpress.page"

    wordpress_id = fields.Many2one('migration.import.wordpress', string="Wordpress Import")
    name = fields.Char(string="Name")
    url = fields.Char(string="URL")
