# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models

class BirthDateAge(models.Model):

    _inherit = "res.partner"

    age = fields.Integer(string="Age")
    
    @api.onchange('birthdate')
    def _onchange_birthdate(self):
        """Updates age field when birth_date is changed"""
        if self.birthdate:
            d1 = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
            
    @api.model
    def update_ages(self):
        """Updates age field for all partners once a day"""
        for rec in self.env['res.partner'].search([]):
            if rec.birthdate:
                d1 = datetime.strptime(rec.birthdate, "%Y-%m-%d").date()
                d2 = date.today()
                rec.age = relativedelta(d2, d1).years