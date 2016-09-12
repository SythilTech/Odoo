# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import openerp.http as http
from openerp.http import request
import requests

from openerp import api, fields, models

class WebsitePageTemplateServer(models.Model):

    _inherit = "ir.ui.view"
    
    is_webpage_template_server = fields.Boolean(string="Webpage Template (Server)")