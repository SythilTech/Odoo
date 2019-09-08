# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemSearchContext(models.Model):

    _name = "sem.search.context"

    type = fields.Selection([('search','Search'),('map','Map')], string="Type")
    keyword = fields.Char(string="Keyword")
    search_engine_id = fields.Many2one('sem.search.engine', string="Search Engine")
    geo_target_name = fields.Char(string="Geo Target Name")
    location_id = fields.Char(string="Location ID", help="The ID of the location within the search engine")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    accuracy_radius_meters = fields.Char(string="Accuracy Radius (Meters)")
    device_id = fields.Many2one('sem.search.device', string="Device")
    map_zoom_level = fields.Char(string="Map Zoom Level")
    search_result_ids = fields.One2many('sem.search.results', 'search_context_id', string="Search Results")

    def perform_search(self):
        search_results = self.search_engine_id.perform_search(self)
        search_results['search_context_id'] = self.id
        self.env['sem.search.results'].create(search_results)

    def get_insight(self):
        return self.search_engine_id.get_insight(self)

class SemSearchContextWizard(models.TransientModel):

    _name = "sem.search.context.wizard"

    website_id = fields.Many2one('sem.client.website', string="Website")
    type = fields.Selection([('search','Search'),('map','Map')], string="Type")
    search_engine_id = fields.Many2one('sem.search.engine', string="Search Engine")
    keyword_ids = fields.One2many('sem.search.context.wizard.keyword', 'wizard_id', string="Keywords")
    device_ids = fields.Many2many('sem.search.device', string="Devices")
    location_string = fields.Char(string="Find Geo Target")
    suggestion_id = fields.Many2one('sem.search.context.wizard.suggestion', string="Suggestions")
    geo_target_ids = fields.Many2many('sem.search.context.wizard.geo', string="Geo Targets")
    map_zoom_level = fields.Char(string="Map Zoom Level")

    @api.onchange('location_string')
    def _onchange_location_string(self):
        if self.search_engine_id and self.location_string:

            # Get the list of locations that the search engine supports using it's API
            geo_targets = self.search_engine_id.find_geo_targets(self.location_string)

            # Now add the records to the pool so they can be selected using the geo_target_ids fields
            for geo_target in geo_targets:
                self.env['sem.search.context.wizard.suggestion'].create(geo_target)

    @api.onchange('suggestion_id')
    def _onchange_suggestion_id(self):
        if self.suggestion_id:
            # Create a geo target with the same information
            wizrd_geo_target = self.env['sem.search.context.wizard.geo'].create({'name': self.suggestion_id.name, 'location_id': self.suggestion_id.location_id, 'latitude': self.suggestion_id.latitude, 'longitude': self.suggestion_id.longitude})

            self.geo_target_ids = [(4, wizrd_geo_target.id)]

            # Clear the suggestions for reuse
            self.location_string = False
            self.suggestion_id = False

    def add_search_contexts(self):

        for keyword in self.keyword_ids:
            for device in self.device_ids:
                for geo_target in self.geo_target_ids:
                    # Create a large amount of search contexts
                    local_search_context = self.env['sem.search.context'].create({'search_engine_id': self.search_engine_id.id, 'location_id': geo_target.location_id, 'device_id': device.id, 'keyword': keyword.name, 'geo_target_name': geo_target.name, 'latitude': geo_target.latitude, 'longitude': geo_target.longitude, 'accuracy_radius_meters': geo_target.accuracy_radius_meters})

                    # Also add the geo targets to the website
                    self.website_id.search_context_ids = [(4, local_search_context.id)]

class SemSearchContextWizardKeyword(models.TransientModel):

    _name = "sem.search.context.wizard.keyword"

    wizard_id = fields.Many2one('sem.search.context.wizard', string="Wizard")
    name = fields.Char(string="Name")

class SemSearchContextWizardSuggestion(models.TransientModel):

    _name = "sem.search.context.wizard.suggestion"

    name = fields.Char(string="Name")
    location_id = fields.Char(string="The reference ID of the location in the Search Engine database")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    accuracy_radius_meters = fields.Char(string="Accuracy Radius (Meters)")

class SemSearchContextWizardGeo(models.TransientModel):

    _name = "sem.search.context.wizard.geo"

    name = fields.Char(string="Name")
    location_id = fields.Char(string="The reference ID of the location in the Search Engine database")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    accuracy_radius_meters = fields.Char(string="Accuracy Radius (Meters)")