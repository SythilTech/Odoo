# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

class SaasModulesBuiltin(models.Model):

    _name = "saas.modules.builtin"
    
    name = fields.Char(string="Database Name")