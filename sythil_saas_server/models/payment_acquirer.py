# -*- coding: utf-8 -*-
import json
import requests
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentAcquirerOAuth(models.Model):

    _inherit = "payment.acquirer"
    
    paypal_client_id = fields.Char(string="Paypal Client ID")
    paypal_secret = fields.Char(string="Paypal Secret")