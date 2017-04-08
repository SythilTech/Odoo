from openerp import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class BirthDateAge(models.Model):

    _inherit = "res.partner"

    birth_date = fields.Date(string="DOB")
    age = fields.Integer(string="Age")

    @api.onchange('birth_date')
    @api.one
    def update_ages_onchange(self):
        if self.birth_date:
            d1 = datetime.strptime(self.birth_date, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years
            
    @api.model
    def update_ages(self):
        for rec in self.env['res.partner'].search([]):
            if rec.birth_date:
                d1 = datetime.strptime(rec.birth_date, "%Y-%m-%d").date()
                d2 = date.today()
                rec.age = relativedelta(d2, d1).years