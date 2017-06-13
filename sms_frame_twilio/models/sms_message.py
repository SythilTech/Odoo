# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from lxml import etree
import logging
_logger = logging.getLogger(__name__)
import base64

from openerp.http import request
from openerp import api, fields, models
from openerp.exceptions import UserError

class sms_response():
     delivary_state = ""
     response_string = ""
     human_read_error = ""
     mms_url = ""
     message_id = ""

class SmsMessageMMS(models.Model):

    _inherit = "sms.message"
    
    media_ids = fields.One2many('sms.message.media', 'sms_id', string='Media List')
    
class SmsMessageMedia(models.Model):

    _name = "sms.message.media"
    
    sms_id = fields.Many2one('sms.message', string="SMS Message")
    data = fields.Binary(string="Data")
    data_filename = fields.Char(string="Filename")
    content_type = fields.Char(string="Content Type")