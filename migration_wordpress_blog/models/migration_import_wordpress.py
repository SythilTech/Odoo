# -*- coding: utf-8 -*-
import requests
import logging
_logger = logging.getLogger(__name__)
import json
from openerp import api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
from lxml import html, etree

class MigrationImportWordpressBlog(models.Model):

    _inherit = "migration.import.wordpress"
    
    blog_post_ids = fields.Many2many('blog.post', string="Imported Blog Posts")
    
    def import_posts(self):
        _logger.error("Import Posts")

        #Get Posts
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/posts")
        blog_json_data = json.loads(response_string.text)

        #Also get media since we will be importing the images in the post
        response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/media")
        media_json_data = json.loads(response_string.text)
        
        for blog_json in blog_json_data:
            title = blog_json['title']['rendered']
            slug = blog_json['slug']
            content = blog_json['content']['rendered']
            status = blog_json['status']
            
            wraped_content = ""
            wraped_content += "<div class=\"container\">\n"
            wraped_content += content.strip()
            wraped_content += "</div>"

            transformed_content = self.transform_post_content(wraped_content)

            #Translate Wordpress published status to the Odoo one
            published = False
            if status == "publish":
                published = True

            external_identifier = "import_post_" + str(blog_json['id'])

            #Create an external ID so we don't reimport the same post again
            blog_post = self.env['ir.model.data'].xmlid_to_object('wordpress_import.' + external_identifier)
            if blog_post:
                #Update the blog post
                blog_post.content = transformed_content
            else:
                #Create the blog post if it does not exist
                blog_post = self.env['blog.post'].create({'blog_id':1, 'name':title, 'content': transformed_content, 'website_published': published})
                
                self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'ir.ui.view', 'res_id': blog_post.id })
                self.blog_post_ids = [(4,blog_post.id)]
