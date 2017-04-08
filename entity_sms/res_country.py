from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime


class res_country_esms(models.Model):

    _inherit = "res.country"
    
    mobile_prefix = fields.Char(string="Mobile Prefix")