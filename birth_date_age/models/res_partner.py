# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models

class BirthDateAge(models.Model):

    _inherit = "res.partner"

    birth_date = fields.Date(string="DOB")
    age = fields.Integer(string="Age")
    
    @api.onchange('birth_date')
    def _onchange_birth_date(self):
        """Updates age field when birth_date is changed"""
        if self.birth_date:
            d1 = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
            
    @api.model
    def update_ages(self):
        """Updates age field for all partners once a day"""
        for rec in self.env['res.partner'].search([]):
            if rec.birth_date:
                d1 = datetime.strptime(rec.birth_date, "%Y-%m-%d").date()
                d2 = date.today()
                rec.age = relativedelta(d2, d1).years