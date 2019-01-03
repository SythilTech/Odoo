# -*- coding: utf-8 -*-

from odoo import api, fields, models

class WebsitePageMigrationWordpress(models.Model):

    _inherit = "website.page"

    wordpress_id = fields.Many2one('migration.import.wordpress', string="Wordpress Import")