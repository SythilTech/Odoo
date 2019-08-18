# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemCheckCategory(models.Model):

    _name = "sem.check.category"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(string="Name")
    check_ids = fields.One2many('sem.check', 'category_id', string="SEO Checks")

    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('sem.check.category')
        values['sequence']=sequence
        return super(SemCheckCategory, self).create(values)