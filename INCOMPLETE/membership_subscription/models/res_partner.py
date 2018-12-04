# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class RespartnerMembership(models.Model):

    _inherit = "res.partner"

    payment_membership_id = fields.Many2one('payment.membership', string="Membership")