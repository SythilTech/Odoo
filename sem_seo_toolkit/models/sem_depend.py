# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemDepend(models.Model):

    _name = "sem.depend"

    name = fields.Char(string="Name")