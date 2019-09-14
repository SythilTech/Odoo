# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemSearchResults(models.Model):

    _name = "sem.search.results"

    search_context_id = fields.Many2one('sem.search.context', string="Search Context")
    raw_data = fields.Text(string="Raw Data")
    search_url = fields.Char(string="Search URL")
    result_ids = fields.One2many('sem.search.results.result', 'results_id', string="Search Results")

    @api.multi
    def competition_report(self):
        self.ensure_one()

        competition_report = self.env['sem.report.competition'].create({'search_results_id': self.id})

        for search_result in self.result_ids:
            seo_report = self.env['sem.tools'].check_url(search_result.url)
            self.env['sem.report.competition.result'].create({'competition_id': competition_report.id, 'search_result_id': search_result.id, 'report_id': seo_report.id})
        
        return {
            'name': 'Competition Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sem.report.competiton',
            'type': 'ir.actions.act_window',
            'res_id': competition_report.id
        }

class SemSearchResultsResult(models.Model):

    _name = "sem.search.results.result"

    results_id = fields.Many2one('sem.search.results', string="Search Results Container")
    position = fields.Integer(string="Position")
    name = fields.Char(string="Name")
    url = fields.Char(string="URL")
    snippet = fields.Char(string="Snippet")