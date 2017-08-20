# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from openerp import api, fields, models
import openerp.http as http
from openerp.http import request

class AttachmentSaasDatabase(models.Model):

    _inherit = "ir.attachment"
    
    saas_database_id = fields.Many2one(string="SAAS Datebase")