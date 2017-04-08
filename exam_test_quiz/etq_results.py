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
    
    exam_id = fields.Many2one('etq.exam', string="Exam", readonly=True)
    results = fields.One2many('etq.result.question', 'result_id', string="Results", readonly=True)
    
class etq_result_question(models.Model):

    _name = "etq.result.question"
    
    result_id = fields.Many2one('etq.result', string="Result", readonly=True)
    question = fields.Many2one('etq.question', string="Question", readonly=True)
    question_options = fields.One2many('etq.result.question.option','question_id',string="Options", readonly=True)
    correct = fields.Boolean(string="Correct", readonly=True)
    question_name = fields.Char(related="question.question", string="Question")
    
class etq_result_question_options(models.Model):

    _name = "etq.result.question.option"
    
    question_id = fields.Many2one('etq.result.question',string="Question ID", readonly=True)
    option_id = fields.Many2one('etq.question.option', string="Option", readonly=True)
    question_options_value = fields.Char(string="Option Value", readonly=True)
    