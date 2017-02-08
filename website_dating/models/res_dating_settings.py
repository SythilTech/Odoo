# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResDatingSettings(models.TransientModel):

    _name = 'res.dating.settings'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)    
    min_dating_age = fields.Integer(related="company_id.min_dating_age", string="Min Registration Age")