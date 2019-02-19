# -*- coding: utf-8 -*-

from odoo import fields, models

class WebsiteManyChat(models.Model):

    _inherit = 'website'

    manychat_id = fields.Many2one('integration.manychat', string="ManyChat Widget Account")