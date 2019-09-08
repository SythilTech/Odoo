# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemSearchResults(models.Model):

    _name = "sem.search.results"

    search_context_id = fields.Many2one('sem.search.context', string="Search Context")
    raw_data = fields.Text(string="Raw Data")
    search_url = fields.Char(string="Search URL")
    result_ids = fields.One2many('sem.search.results.result', 'results_id', string="Search Results")

class SemSearchResultsResult(models.Model):

    _name = "sem.search.results.result"

    results_id = fields.Many2one('sem.search.results', string="Search Results Container")
    name = fields.Char(string="Name")
    url = fields.Char(string="URL")
    snippet = fields.Char(string="Snippet")