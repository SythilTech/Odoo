# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SemReportSeo(models.Model):

    _name = "sem.report.seo"
    _rec_name = "keyword"

    client_id = fields.Many2one('sem.client', string="Client")
    url = fields.Char(string="URL")
    keyword = fields.Char(string="Keyword")
    check_ids = fields.One2many('sem.report.seo.check', 'report_id', string="Checks")

class SemReportSeoCheck(models.Model):

    _name = "sem.report.seo.check"

    report_id = fields.Many2one('sem.report.seo', string="SEO Report")
    check_id = fields.Many2one('sem.check', string="SEO Check")
    check_pass = fields.Boolean(string="Pass", help="Did it pass or fail this check/test")
    notes = fields.Html(sanitize=False, string="Notes", help="Any additional information")
    time = fields.Float(string="Processing Time")

class SemReportCompetition(models.Model):

    _name = "sem.report.competition"

    client_id = fields.Many2one('sem.client', string="Client")
    ranking_ids = fields.One2many('sem.report.competition.ranking', 'competition_id', string="Rankings")

class SemReportCompetitionRanking(models.Model):

    _name = "sem.report.competition.ranking"

    competition_id = fields.Many2one('sem.report.competition', string="Competition")
    engine_id = fields.Many2one('sem.search_engine', string="Search Engine")
    locale = fields.Char(string="Locale", help="Search results can vary by device and location")
    keyword = fields.Char(string="Keyword")
    position = fields.Integer(string="Position")
    title = fields.Char(string="Title")
    link = fields.Char(string="Link")
    snippet = fields.Text(string="Snippet")

class SemReportRanking(models.Model):

    _name = "sem.report.ranking"

    website_id = fields.Many2one('sem.client.website', string="Client Website")
    result_ids = fields.One2many('sem.report.ranking.result', 'ranking_id', string="Results")

class SemReportRankingResult(models.Model):

    _name = "sem.report.ranking.result"

    ranking_id = fields.Many2one('sem.report.ranking', string="Ranking Report")
    keyword_id = fields.Many2one('sem.client.website.keyword', string="Keyword")
    geo_target_id = fields.Many2one('sem.geo_target', string="Geo Target")
    rank = fields.Integer(string="Rank")
    search_url = fields.Char(string="Search URL")
    link_url = fields.Char(string="Link URL")
    search_html = fields.Char(string="Search HTML")

class SemReportMetric(models.Model):

    _name = "sem.report.metric"

    url = fields.Char(string="URL")
    result_ids = fields.One2many('sem.report.metric.result', 'report_metric_id', string="Results")

class SemReportMetricResults(models.Model):

    _name = "sem.report.metric.result"

    report_metric_id = fields.Many2one('sem.report.metric', string="SEO Metric")
    metric_id = fields.Many2one('sem.metric', string="Metric")
    value = fields.Char(string="Value")

class SemReportSearch(models.Model):

    _name = "sem.report.search"

    website_id = fields.Many2one('sem.client.website', string="Client Website")
    result_ids = fields.One2many('sem.report.search.result', 'search_id', string="Results")

class SemReportSearchResult(models.Model):

    _name = "sem.report.search.result"

    search_id = fields.Many2one('sem.report.search', string="Search Report")
    keyword_id = fields.Many2one('sem.client.website.keyword', string="Keyword")
    geo_target_id = fields.Many2one('sem.geo_target', string="Geo Target")
    monthly_searches = fields.Char(string="Monthly Searches")
    competition = fields.Char(string="Competition")