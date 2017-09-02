# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerDirectory(models.Model):

    _inherit = "res.country.state"

    listing_count = fields.Integer(string="Listing Count", compute="_compute_listing_count", store=True)
    listing_ids = fields.One2many('res.partner','state_id', string="State Listings", domain=[('in_directory','=',True)])

    @api.one
    @api.depends('listing_ids')
    def _compute_listing_count(self):
        self.listing_count = len(self.listing_ids)