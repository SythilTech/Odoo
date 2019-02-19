# -*- coding: utf-8 -*-

from odoo import fields, models

class CrmLeadTagManyChat(models.Model):

    _inherit = 'crm.lead.tag'

    manychat_id = fields.Char(string="ManyChat ID")