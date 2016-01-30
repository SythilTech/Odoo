# -*- coding: utf-8 -*-
import unicodedata
import re

from openerp import api, fields, models
from openerp.http import request
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web

from openerp.addons.website.models.website import slug

class WebsiteSupportHelpGroups(models.Model):

    _name = "website.support.help.groups"
    
    name = fields.Char(string="Help Group")
    page_ids = fields.One2many('website.support.help.page','group_id',string="Pages")
    page_count = fields.Integer(string="Number of Pages", computed='_page_count')
    
    @api.one
    @api.depends('page_ids')
    def _page_count(self):
        """"Amount of help pages in a help group"""
        self.page_count = self.env['website.support.help.page'].search_count([('group_id','=',self.id)])
    
class WebsiteSupportHelpPage(models.Model):

    _name = "website.support.help.page"
    _order = "name asc"
    
    name = fields.Char(string='Page Name')
    url = fields.Char(string="Page URL")
    url_generated = fields.Char(string="URL", compute='_compute_url_generated')
    group_id = fields.Many2one('website.support.help.groups', string="Group")
    content = fields.Html(sanatize=False, string='Content')
    
    @api.one
    @api.depends('name')
    def _compute_url_generated(self):
        self.url_generated = "/support/help/" + slug(self.group_id) + "/" + slug(self)    
    
def slugify(s, max_length=None):
    """ Transform a string to a slug that can be used in a url path.

    This method will first try to do the job with python-slugify if present.
    Otherwise it will process string by stripping leading and ending spaces,
    converting unicode chars to ascii, lowering all chars and replacing spaces
    and underscore with hyphen "-".

    :param s: str
    :param max_length: int
    :rtype: str
    """
    s = ustr(s)
    uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    slug = re.sub('[\W_]', ' ', uni).strip().lower()
    slug = re.sub('[-\s]+', '-', slug)

    return slug[:max_length]
