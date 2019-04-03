# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResUsersDirectory(models.Model):

    _inherit = "res.users"

    directory_level_id = fields.Many2one('res.users.directory.level', string="Directory Level")

class ResUsersLevelDirectory(models.Model):

    _name = "res.users.directory.level"

    name = fields.Char(string="Name")
    free_listing_limit = fields.Integer(string="Free Listing Limit")