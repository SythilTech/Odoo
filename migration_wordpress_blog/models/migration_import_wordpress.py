# -*- coding: utf-8 -*-
import requests
import logging
_logger = logging.getLogger(__name__)
import json
from openerp import api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
from HTMLParser import HTMLParser
from lxml import html, etree

class MigrationImportWordpressBlog(models.Model):

    _inherit = "migration.import.wordpress"
    
    blog_post_ids = fields.Many2many('blog.post', string="Imported Blog Posts")
    
    def import_posts(self):
        _logger.error("Import Posts")

        #Get Posts
        blog_json_data = self.pagination_requests(self.wordpress_url + "/wp-json/wp/v2/posts")
        
        #Also get media since we will be importing the images in the post
        media_json_data = self.pagination_requests(self.wordpress_url + "/wp-json/wp/v2/media")
        
        #Get Posts
        tax_response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/posts")
        tax_json_data = json.loads(tax_response_string.text)
        
        for blog_json in blog_json_data:
            h = HTMLParser()
            title = h.unescape(blog_json['title']['rendered'])
            slug = blog_json['slug']
            content = blog_json['content']['rendered']
            status = blog_json['status']
                        
            wraped_content = ""
            wraped_content += "<div class=\"container\">\n"
            wraped_content += content.strip()
            wraped_content += "</div>"

            transformed_content = self.transform_post_content(wraped_content, media_json_data)

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
                #We also get the Wordpress user and import it if neccassary
                wordpress_user = self.env['ir.model.data'].xmlid_to_object('wordpress_import.import_user_' + str(blog_json['author']) )
                if wordpress_user:
                    _logger.error("TODO implement reimport user code")
                else:
                    user_response_string = requests.get(self.wordpress_url + "/wp-json/wp/v2/users/" + str(blog_json['author']) )
                    user_json = json.loads(user_response_string.text)
                    wordpress_user = self.transfer_user(user_json)

                #Create the blog post if it does not exist
                blog_post = self.env['blog.post'].sudo(wordpress_user.id).create({'author_id': wordpress_user.partner_id.id, 'write_uid': wordpress_user.id, 'blog_id':1, 'name':title, 'content': transformed_content, 'website_published': published})
                
                self.env['ir.model.data'].create({'module': "wordpress_import", 'name': external_identifier, 'model': 'blog.post', 'res_id': blog_post.id })
                self.blog_post_ids = [(4,blog_post.id)]
