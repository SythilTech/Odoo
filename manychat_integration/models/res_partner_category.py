# -*- coding: utf-8 -*-

from odoo import fields, models

class RespartnerCategoryManyChat(models.Model):

    _inherit = 'res.partner.category'

    manychat_id = fields.Char(string="ManyChat Tag")