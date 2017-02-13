# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResCompanyCloudTasks(models.Model):

    _inherit = "res.company"
    
    firebase_auth_key = fields.Char(string="FireBase Auth Key")