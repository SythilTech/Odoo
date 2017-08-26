# -*- coding: utf-8 -*-
import requests
from lxml import html, etree
import openerp
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class WebsiteStyleManager(models.Model):

    _inherit = "website"
    
    tag_styles = fields.One2many('website.style', 'website_id', string="HTML Tag Styles")
    css_text = fields.Text(string="CSS Text")
    custom_css = fields.Text(string="Custom CSS", help="Define website wide styles and classes")
    force_styles = fields.Boolean(string="Force Styles", help="Applies an !important to all styles forcing the style over higher specificity")
    color_profile = fields.Many2one('website.style.profile', string="Color Profile")
    custom_less_ids = fields.One2many('website.style.less', 'website_id', string="LESS Variables")

    @api.onchange('color_profile')
    def _onchange_color_profile(self):

        if self.color_profile:

            self.custom_less_ids.unlink()
            for less_style in self.color_profile.custom_less_ids:

                self.env['website.style.less'].create({'website_id': 1, 'name': less_style.name, 'internal_name': less_style.internal_name, 'value': less_style.value})

    @api.one
    def generate_less(self):
        module_directory = openerp.modules.get_module_path("website_style_manager")
        full_path = module_directory + "/static/src/less/override.less"
        
        less_data = ""
        for less_style in self.custom_less_ids:
            less_data += "@" + str(less_style.internal_name) + ": " + str(less_style.value) + ";\n"
        
        with open(full_path, "w") as less_file:
            less_file.write(less_data)

    
    @api.onchange('tag_styles', 'force_styles')
    def _onchange_tag_styles(self):
        self.css_text = ""
        for style in self.tag_styles:
            self.css_text += style.html_tag.html_tag + " {\n"
            
            if style.font_family:
                self.css_text += "    font-family: '" + style.font_family.name + "'"
                if self.force_styles:
                    self.css_text += " !important"
                self.css_text += ";\n"
    
            if style.font_color:
                self.css_text += "    color: " + style.font_color
                if self.force_styles:
                    self.css_text += " !important"
                self.css_text += ";\n"

            if style.font_size:
                self.css_text += "    font-size: " + style.font_size
                if self.force_styles:
                    self.css_text += " !important"
                self.css_text += ";\n"
 
            self.css_text += "}\n\n"
    
class WebsiteStyle(models.Model):

    _name = "website.style"
    
    website_id = fields.Many2one('website', string="Website")
    html_tag = fields.Many2one('website.style.htmltag', string="HTML Tag", required=True)
    font_family = fields.Many2one('website.style.fontfamily', string="Font Family")
    font_color = fields.Char(string="Font Color", default="#000000")
    font_size = fields.Char(string="Font Size", help="The Size of the font, please include the suffix", default="16px")

class WebsiteStyleProfile(models.Model):

    _name = "website.style.profile"
    
    name = fields.Char(string="Profile Name")
    custom_less_ids = fields.One2many('website.style.profile.less', 'profile_id', string="LESS Variables")

class WebsiteStyleProfileLess(models.Model):

    _name = "website.style.profile.less"
    
    profile_id = fields.Many2one('website.style.profile', string="Profile")
    name = fields.Char(string="Display Name", help="Display name of the less variable")
    internal_name = fields.Char(string="Internal Name", help="The actually name of the less variable", required=True)
    value = fields.Char(string="Value", help="Color HEX code", required=True)
    
    
class WebsiteStyleLess(models.Model):

    _name = "website.style.less"
    
    website_id = fields.Many2one('website', string="Website")
    name = fields.Char(string="Name", help="Display name of the less variable")
    internal_name = fields.Char(string="Internal Name", help="The actually name of the less variable", required=True)
    value = fields.Char(string="Value", help="Color HEX code", required=True)
    
class WebsiteStyleHTMLTag(models.Model):

    _name = "website.style.htmltag"
    
    style_id = fields.Many2one('website.style', string="Website Style")
    name = fields.Char(string="Name")
    html_tag = fields.Char(string="HTML Tag", help="Name is for fancy display 'Heading 1' this is the actual tag 'h1'")
    
class WebsiteStyleFontFamily(models.Model):

    _name = "website.style.fontfamily"
    
    style_id = fields.Many2one('website.style', string="Website Style")
    name = fields.Char(string="Font Family")
    
class WebsiteStyleFontSize(models.Model):

    _name = "website.style.fontsize"
    
    style_id = fields.Many2one('website.style', string="Website Style")
    name = fields.Char(string="Font Size", help="The Size of the font, please have em, px, % or pt suffix", default="12px")