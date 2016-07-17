# -*- coding: utf-8 -*
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from openerp import api, fields, models

class ResDatingQuestionnaire(models.Model):

    _name = "res.dating.questionnaire"
    _description = "Dating Questionaire"
    
    name = fields.Char(string="Name")
    question_ids = fields.One2many('res.dating.questionnaire.question', 'questionnaire_id', string='Questions')
    matching_rule_ids = fields.One2many('res.dating.questionnaire.matchingrules', 'questionnaire_question_id', string="Matching Rules", help="e.g. person puts 'tall' as height matches with people partner who put 'tall' as preferred partner height")
    
    @api.one
    def create_fake_questionnaire_answers(self):
        dating_partners = self.env['res.partner'].search([('dating','=',True)])
        
        #Go through each fake dating profile and create a fake questionnaire answer
        for dating_partner in dating_partners:
            new_questionnaire_answer = self.env['res.dating.questionnaire.answer'].create({'questionnaire_id': self.id, 'partner_id':dating_partner.id})

            #Go through each question in this questionnaire and choose a random option
            for question in self.env['res.dating.questionnaire.question'].search([('questionnaire_id','=',self.id)]):
                question_options = self.env['res.dating.questionnaire.question.option'].search([('question_id','=',question.id)])
                option_count = len(question_options)
                random_option = question_options[randint(0, option_count - 1)]
                self.env['res.dating.questionnaire.answer.question'].create({'questionnaire_answer_id': new_questionnaire_answer.id, 'question_id': question.id, 'option_id':random_option.id})
    
class ResDatingQuestionnaireQuestion(models.Model):

    _name = "res.dating.questionnaire.question"
    _description = "Dating Questionaire Question"
    
    questionnaire_id = fields.Many2one('res.dating.questionnaire', string='Questionnaire')
    type = fields.Selection([('single_answer','Single Answer')], string="Type", default="single_answer")
    name = fields.Char(string="Question Text")
    option_ids = fields.One2many('res.dating.questionnaire.question.option', 'question_id', string="Options")
    
class ResDatingQuestionnaireQuestionOption(models.Model):

    _name = "res.dating.questionnaire.question.option"
    _description = "Dating Questionaire Question"
    
    question_id = fields.Many2one('res.dating.questionnaire.question', string='Question')
    name = fields.Char(string="Question Text")
    
class ResDatingQuestionnaireMatchingRules(models.Model):

    _name = "res.dating.questionnaire.matchingrules"
    _description = "Dating Questionaire Matching Rules"
    
    questionnaire_question_id = fields.Many2one('res.dating.questionnaire', string="Questionnaire")
    type = fields.Selection([('option_match','Option Match')], string="Type", default="option_match")
    question_compare_id = fields.Many2one('res.dating.questionnaire.question', string="Question Compare")
    question_compare_option_id = fields.Many2one('res.dating.questionnaire.question.option', string="Question Compare Option", domain="[('question_id','=',question_compare_id)]")
    question_match_id = fields.Many2one('res.dating.questionnaire.question', string="Question Match")
    question_match_option_id = fields.Many2one('res.dating.questionnaire.question.option', string="Question Match Option", domain="[('question_id','=',question_match_id)]")
    option = fields.Selection([('match','Match'), ('penalise','Penalise'), ('exclude','Exclude')],string="Option", default="match", help="Match: add points\nPenalise: remove points\nExclude:instantly incompatible partners")
    weight = fields.Integer(string="Weight", help="How important this rule is\ne.g. tall pref->tall height=10\ntall pref->average height=3")