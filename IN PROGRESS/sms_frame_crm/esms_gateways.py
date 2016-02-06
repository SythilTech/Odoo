from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class esms_gateways(models.Model):

    _name = "esms.gateways"
    
    name = fields.Char(required=True, string='Gateway Name')
    gateway_model_name = fields.Char(required='True', string='Gateway Model Name')