# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettingsManyChat(models.TransientModel):

    _inherit = 'res.config.settings'

    manychat_id = fields.Many2one('integration.manychat', related='website_id.manychat_id', string="ManyChat Widget Account/Page", help="The account/page which any ManyChat widgets are bound to")