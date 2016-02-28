# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerWebsiteDating(models.Model):

    _inherit = "event.event"

    dating_event = fields.Boolean(string="Dating Event")
    min_age = fields.Integer(string="Min Age", default="18")
    max_age = fields.Integer(string="Max Age", default="60")
    current_males = fields.Integer(string="Current Males")
    current_females = fields.Integer(string="Current Females")
    max_male = fields.Integer(string="Max Males", default="5")
    max_female = fields.Integer(string="Max Females", default="5")
    dating_description = fields.Text(string="Event Description")