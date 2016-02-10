# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SaasPartner(models.Model):

    _inherit = "res.partner"

    saas_partner = fields.Boolean(string="SAAS Partner")
    saas_database = fields.Char(string="SAAS Database")
    saas_password = fields.Char(string="SAAS Password")