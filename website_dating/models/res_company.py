# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResCompanyDating(models.Model):

    _inherit = "res.company"
    
    min_dating_age = fields.Integer(string="Min Registration Age", default="18")