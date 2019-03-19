# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResUsersManyChat(models.Model):

    _inherit = 'res.users'

    manychat_id = fields.Char(string="ManyChat ID")