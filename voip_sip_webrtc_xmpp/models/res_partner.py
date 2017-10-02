# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerXMPP(models.Model):

    _inherit = "res.partner"
    
    xmpp_address  = fields.Char(string="XMPP Address")