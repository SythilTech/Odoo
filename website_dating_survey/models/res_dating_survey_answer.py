# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResDatingSurveyAnswer(models.Model):

    _name = "res.dating.survey.answer"
    _description = "Dating Survey Answer"
    
    survey_id = fields.Many2one('res.dating.survey', string="Survey")
    partner_id = fields.Many2one('res.partner', string="Partner")
    question_ids = fields.One2many('res.dating.survey.answer.question', 'survey_answer_id', string='Questions')
    survey_token = fields.Char(string="Survey Token")
    state = fields.Selection([('incomplete','Incomplete'),('complete','Complete')], string="State")
    
class ResDatingSurveyAnswerQuestion(models.Model):

    _name = "res.dating.survey.answer.question"
    _description = "Dating Survey Answer Question"
    
    survey_answer_id = fields.Many2one('res.dating.survey.answer', string='Survey Answer')
    question_id = fields.Many2one('res.dating.survey.page.question', string='Question', readonly="True")
    option_id = fields.Many2one('res.dating.survey.page.question.option', string="Option", readonly="True")
    value = fields.Char(string="Answer Value")