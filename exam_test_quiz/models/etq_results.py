from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
from datetime import datetime
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import unicodedata
import re

class etq_results(models.Model):

    _name = "etq.result"
    _description = "Exam Result"
    
    exam_id = fields.Many2one('etq.exam', string="Exam", readonly=True)
    user_id = fields.Many2one('res.users', string="User")
    score = fields.Char(string="Score", compute="_compute_score")
    results = fields.One2many('etq.result.question', 'result_id', string="Results", readonly=True)
    token = fields.Char(string="Token")
    state = fields.Selection([('incomplete','Incomplete'), ('complete','Complete')], string="State")
    
    @api.one
    @api.depends('results')
    def _compute_score(self):
         num_questions = self.env['etq.result.question'].search_count([('result_id', '=', self.id)])
         correct_questions = self.env['etq.result.question'].search_count([('result_id', '=', self.id), ('correct', '=', True)])
         self.score = str(correct_questions) + "/" + str(num_questions) + " " + str( float( float(correct_questions) / float(num_questions) ) * 100) + "%"
         
class etq_result_question(models.Model):

    _name = "etq.result.question"
    _description = "Exam Result Question"
    
    result_id = fields.Many2one('etq.result', string="Result", readonly=True)
    question = fields.Many2one('etq.question', string="Question", readonly=True)
    question_options = fields.One2many('etq.result.question.option','question_id',string="Options", readonly=True)
    correct = fields.Boolean(string="Correct", readonly=True)
    question_name = fields.Html(related="question.question", string="Question")
    
class etq_result_question_options(models.Model):

    _name = "etq.result.question.option"
    _desciption = "Exam Result Question Option"
    
    question_id = fields.Many2one('etq.result.question',string="Question ID", readonly=True)
    option_id = fields.Many2one('etq.question.option', string="Option", readonly=True)
    option_name = fields.Char(related="option_id.option", string="Option")
    question_options_value = fields.Char(string="Option Value", readonly=True)
    