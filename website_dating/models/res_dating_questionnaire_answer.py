# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResDatingQuestionnaireAnswer(models.Model):

    _name = "res.dating.questionnaire.answer"
    _description = "Dating Questionaire Answer"
    
    questionnaire_id = fields.Many2one('res.dating.questionnaire', string="Questionnaire")
    partner_id = fields.Many2one('res.partner', string="Partner")
    question_ids = fields.One2many('res.dating.questionnaire.answer.question', 'questionnaire_answer_id', string='Questions')
    
class ResDatingQuestionnaireAnswerQuestion(models.Model):

    _name = "res.dating.questionnaire.answer.question"
    _description = "Dating Questionaire Answer Question"
    
    questionnaire_answer_id = fields.Many2one('res.dating.questionnaire.answer', string='Questionnaire Answer')
    question_id = fields.Many2one('res.dating.questionnaire.question', string='Question', readonly="True")
    option_id = fields.Many2one('res.dating.questionnaire.question.option', string="Option", readonly="True")