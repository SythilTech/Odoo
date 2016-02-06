# -*- coding: utf-8 -*-
import unicodedata
import re

from openerp import api, fields, models
from openerp.http import request
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web

class SaasDatabase(models.Model):

    _name = "saas.database"
    
    name = fields.Char(string="Database Name")
