# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models

class WebsiteDirectoryTemplate(models.Model):

    _name = "website.directory.template"
    
    name = fields.Char(string="Name")
    website_active = fields.Boolean(string="Active")
    description = fields.Text(string="Description")
    page_ids = fields.One2many('website.directory.template.page', 'template_id', string="Pages")

    def set_active(self):
        # Find the default template and revert all pages back to the default
        default_template = self.env['ir.model.data'].get_object('website_business_directory','website_directory_template_default')

        for page in default_template.page_ids:
            page.page_id.view_id = page.view_id.id

        # Now change the views of only the pages in the template with any non included pages remaining the default
        for page in self.page_ids:
            page.page_id.view_id = page.view_id.id

        # Deactivate the previously active template (can be multiple active if glitched)
        for active_template in self.env['website.directory.template'].search([('website_active','=',True)]):
            active_template.website_active = False

        self.website_active = True

class WebsiteDirectoryTemplatePage(models.Model):

    _name = "website.directory.template.page"

    template_id = fields.Many2one('website.directory.template', string="Template")
    page_id = fields.Many2one('website.page', string="Page")
    view_id = fields.Many2one('ir.ui.view', string="View")