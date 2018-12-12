# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class WebsiteMenu(models.Model):

    _inherit = "website.menu"

    group_ids = fields.Many2many('res.groups', string="Access Groups")