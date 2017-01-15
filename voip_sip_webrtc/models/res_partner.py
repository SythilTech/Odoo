# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerVoip(models.Model):

    _inherit = "res.partner"
    
    sip_address  = fields.Char(string="SIP Address")