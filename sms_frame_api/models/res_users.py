# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResUserSmsApi(models.Model):

    _inherit = "res.users"
    
    sms_rest_key = fields.Char(string="REST API Key")
    sms_account_id = fields.Many2one('sms.account', string="SMS Account")