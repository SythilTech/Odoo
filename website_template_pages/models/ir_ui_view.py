# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import openerp.http as http
from openerp.http import request
import requests

from openerp import api, fields, models

class WebsitePageTemplate(models.Model):

    _inherit = "ir.ui.view"
        
    image = fields.Binary(string="Image (Obsolete)")
    is_webpage_template = fields.Boolean(string="Webpage Template")
    template_online = fields.Boolean(string="Webpage Template Online")