# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemGeoTarget(models.Model):

    #TODO rename to search context as device user agent and map zoom level have nothing to do with a geograpic location
    _name = "sem.geo_target"

    def _default_device_id(self):
        return self.env['ir.model.data'].get_object('sem_seo_toolkit', 'sem_device_desktop')

    search_engine_id = fields.Many2one('sem.search_engine', string="Search Engine")
    name = fields.Char(string="Name", help="A human meaningful name to describe the geographic location / search context")
    location_id = fields.Char(string="Location ID", help="The ID of the location within the search engine")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    accuracy_radius_meters = fields.Float(string="Accuracy Radius (Meters)")
    device_id = fields.Many2one('sem.geo_target.device', default=_default_device_id, string="Device")
    map_zoom_level = fields.Integer(default=14, string="Map Zoom Level")

    def get_ranking(self, domain, keyword):
        return self.search_engine_id.get_ranking(self, domain, keyword)

class SemGeoTargetDevice(models.Model):

    _name = "sem.geo_target.device"

    name = fields.Char(string="Name")
    user_agent = fields.Char(string="User Agent")

class SemGeoTargetWizard(models.TransientModel):

    _name = "sem.geo_target.wizard"

    keyword_id = fields.Many2one('sem.client.website.keyword', string="")
    search_engine_id = fields.Many2one('sem.search_engine', string="Search Engine")
    location_string = fields.Char(string="Find Geo Target")
    geo_target_ids = fields.Many2many('sem.geo_target.wizard.record', string="Geo Targets")

    @api.onchange('location_string')
    def _onchange_location_string(self):
        if self.search_engine_id and self.location_string:

            # Get the list of locations that the search engine supports using it's API
            geo_targets = self.search_engine_id.find_geo_targets(self.location_string)

            # Now add the records to the pool so they can be selected using the geo_target_ids fields
            for geo_target in geo_targets:
                self.env['sem.geo_target.wizard.record'].create(geo_target)

    def add_geo_locations(self):

        for geo_target in self.geo_target_ids:
            # Add the geo target to the local cache so it is easy to select locale for future keywords
            local_geo_target = self.env['sem.geo_target'].create({'search_engine_id': self.search_engine_id.id, 'location_id': geo_target.location_id, 'name': geo_target.name, 'latitude': geo_target.latitude, 'longitude': geo_target.longitude, 'accuracy_radius_meters': geo_target.accuracy_radius_meters})

            # Also add the geo targets to the keyword
            self.keyword_id.geo_target_ids = [(4, local_geo_target.id)]

class SemGeoTargetWizardRecord(models.TransientModel):

    _name = "sem.geo_target.wizard.record"

    location_id = fields.Char(string="The reference ID of the location in the Search Engine database")
    name = fields.Char(string="Name")
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    accuracy_radius_meters = fields.Float(string="Accuracy Radius (Meters)")