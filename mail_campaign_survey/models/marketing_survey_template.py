# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import api, fields, models

class MarketingSurveyTemplate(models.Model):

    _name = "marketing.survey.template"
    #_inherit = "mail.compose.message"
    _rec_name = "name"

    def _default_email_from(self):
        return self.env.user.email
    
    name = fields.Char(string="Name", related="survey_id.title")
    survey_id = fields.Many2one('survey.survey', string="Survey", required="True")
    subject = fields.Char(string="Subject", required="True")
    body = fields.Html(string="Contents", required="True")
    email_from = fields.Char(string="From Email", default=_default_email_from)
    
    @api.onchange('survey_id')
    def _onchange_survey_id(self):
        if self.survey_id:
            self.subject = self.survey_id.title
            survey_template = self.env['ir.model.data'].get_object('survey', 'email_template_survey')
       	    self.body = survey_template.body_html