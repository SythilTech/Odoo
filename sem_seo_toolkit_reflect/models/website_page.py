# -*- coding: utf-8 -*-

from odoo import api, fields, models

class WebsitePage(models.Model):

    _inherit = "website.page"

    canonical_url = fields.Char(string="Canonical Url")