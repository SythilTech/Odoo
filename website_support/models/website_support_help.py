# -*- coding: utf-8 -*-
import unicodedata
import re

from openerp import api, fields, models
from openerp.http import request
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web


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
    group_id = fields.Many2one('website.support.help.groups', string="Group")
    
    @api.one
    @api.onchange('name')
    def _page_url(self):
        """Generates the url of the help page (will be become obsolete when 'New Support Page' gets added to website builder"""
        self.url = request.httprequest.host_url + 'support/help/' + slugify(self.name)

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
