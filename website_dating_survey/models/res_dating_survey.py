# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint
from odoo.addons.website.models.website import slug
from openerp import api, fields, models

class ResDatingSurvey(models.Model):

    _name = "res.dating.survey"
    _description = "Dating Survey"
    
    name = fields.Char(string="Name")
    page_ids = fields.One2many('res.dating.survey.page', 'survey_id', string="Pages")

    @api.multi
    def survey_preview(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Dating Survey",
            'target': 'self',
            'url': "/dating/survey/" + slug(self)
        }
            
    @api.one
    def create_fake_survey_answers(self):
        dating_partners = self.env['res.partner'].search([('dating','=',True), ('fake_profile', '=', True)])
        
        #Go through each fake dating profile and create a fake questionnaire answer
        for dating_partner in dating_partners:
            new_questionnaire_answer = self.env['res.dating.survey.answer'].create({'survey_id': self.id, 'partner_id':dating_partner.id})

            #Go through each question in this questionnaire and choose a random option
            for question in self.env['res.dating.survey.page.question'].search([('questionnaire_id','=',self.id)]):
                question_options = self.env['res.dating.questionnaire.question.option'].search([('question_id','=',question.id)])
                option_count = len(question_options)
                random_option = question_options[randint(0, option_count - 1)]
                self.env['res.dating.questionnaire.answer.question'].create({'questionnaire_answer_id': new_questionnaire_answer.id, 'question_id': question.id, 'option_id':random_option.id})

class ResDatingSurveyPage(models.Model):

    _name = "res.dating.survey.page"
    _description = "Dating Survey Page"
    
    survey_id = fields.Many2one('res.dating.survey', string='Survey')
    name = fields.Char(string="Name")
    question_ids = fields.One2many('res.dating.survey.page.question', 'page_id', string='Questions')
    
class ResDatingSurveyPageQuestion(models.Model):

    _name = "res.dating.survey.page.question"
    _description = "Dating Survey Page Question"
    
    page_id = fields.Many2one('res.dating.survey.page', string='Survey Page')
    partner_field_id = fields.Many2one('ir.model.fields', domain=[('model_id','=','res.partner')], string="Field", help="if set data gets saved back to the member")
    type = fields.Selection([('single_answer','Single Answer')], required=True, string="Type", default="single_answer")
    name = fields.Char(string="Question Text", required=True)
    option_ids = fields.One2many('res.dating.survey.page.question.option', 'question_id', string="Options")
    
class ResDatingSurveyPageQuestionOption(models.Model):

    _name = "res.dating.survey.page.question.option"
    _description = "Dating Survey Page Question Option"
    
    question_id = fields.Many2one('res.dating.survey.page.question', string='Question')
    name = fields.Char(string="Option Text", required=True)
    value = fields.Char(string="Option Value", required=True)