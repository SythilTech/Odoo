# -*- coding: utf-8 -*-
from openerp import api, fields, models

class VoipTranscriber(models.Model):

    _name = 'voip.transcriber'
            
    name = fields.Char(string="Name")
    api_key = fields.Char(string="API Key")
    internal_code = fields.Char(string="Internal Code")