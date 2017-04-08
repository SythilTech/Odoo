from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class esms_autoresponse(models.Model):

    _name = "esms.autoresponse"
    
    from_mobile = fields.Char(string='Mobile Number', required=True)
    keyword = fields.Char(string="Keyword", required=True)
    sms_content = fields.Char(string="SMS Message", reqquired=True)