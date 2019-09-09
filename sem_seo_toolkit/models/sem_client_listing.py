# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemClientListing(models.Model):

    _name = "sem.client.listing"

    client_id = fields.Many2one('sem.client', string="SEM Client")
    search_engine_id = fields.Many2one('sem.search.engine', string="Search Engine")
    name = fields.Char(string="Name")
    listing_external_id = fields.Char(string="Listing External ID", help="This is the unique name or ID of the listing in the search engine")
    media_ids = fields.One2many('sem.client.listing.media', 'listing_id', string="Media")
    search_context_ids = fields.Many2many('sem.search.context', string="Search Contexts")

    @api.multi
    def add_search_context(self):
        self.ensure_one()

        return {
            'name': 'Create Search Context',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.search.context.wizard',
            'target': 'new',
            'context': {'default_type': 'map', 'default_search_engine_id': self.search_engine_id.id},
            'type': 'ir.actions.act_window'
        }

class SemClientListingMedia(models.Model):

    _name = "sem.client.listing.media"

    listing_id = fields.Many2one('sem.client.listing', string="Listing")
    image = fields.Binary(string="Image")
    media_external_id = fields.Char(string="Media External ID", help="This is the unique name or ID of the media")