from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
from datetime import datetime
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import unicodedata
import re

class EtqExam(models.Model):

    _name = "etq.exam"
    
    name = fields.Char(string="Name", translate=True)
    slug = fields.Char(string="Slug", compute="slug_me", store="True")
    show_correct_questions = fields.Boolean(string="Show Correct Answers?")
    questions = fields.One2many('etq.question','exam_id', string="Questions")
    fill_mode = fields.Selection([('all','All Questions'),('random','Random')], string="Fill Mode", default="all")
    fill_mode_random_number = fields.Integer(string="Number of Random Questions")

    @api.onchange('fill_mode')
    def _onchange_fill_mode(self):
        if self.fill_mode == "random":
            self.fill_mode_random_number = len(self.questions)
    
    @api.multi
    def view_quiz(self):
        quiz_url = request.httprequest.host_url + "exam/" + str(self.slug)
        return {
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
                  'url'      : quiz_url
               }        
       
    @api.one
    @api.depends('name')
    def slug_me(self):
        if self.name:
            s = ustr(self.name)
            uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
            slug = re.sub('[\W_]', ' ', uni).strip().lower()
            slug = re.sub('[-\s]+', '-', slug)
            
            self.slug = slug
    
class EtqQuestion(models.Model):

    _name = "etq.question"
    _rec_name = "question"
    
    exam_id = fields.Many2one('etq.exam',string="Exam ID")
    image = fields.Binary(string="Image")
    question = fields.Html(string="Question")
    question_rendered = fields.Html(string="Question Render", compute="render_question", sanitize=False)
    question_type = fields.Selection((('multi_choice','Multiple Choice'), ('fill_blank','Fill in the Blank')), default="multi_choice", string="Question Type")
    question_options = fields.One2many('etq.question.option','question_id',string="Multiple Choice Options")
    question_options_blank = fields.One2many('etq.question.optionblank','question_id',string="Fill in the Blank Options")    
    num_options = fields.Integer(string="Options",compute="calc_options")
    num_correct = fields.Integer(string="Correct Options",compute="calc_correct")

    @api.one
    @api.depends('question')
    def render_question(self):
        if self.question:
            temp_string = self.question
            
            temp_string = temp_string.replace("{1}","<i><input name=\"question" + str(self.id) + "option1\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{2}","<i><input name=\"question" + str(self.id) + "option2\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{3}","<i><input name=\"question" + str(self.id) + "option3\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{4}","<i><input name=\"question" + str(self.id) + "option4\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{5}","<i><input name=\"question" + str(self.id) + "option5\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{6}","<i><input name=\"question" + str(self.id) + "option6\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{7}","<i><input name=\"question" + str(self.id) + "option7\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{8}","<i><input name=\"question" + str(self.id) + "option8\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{9}","<i><input name=\"question" + str(self.id) + "option9\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            self.question_rendered = temp_string
            
            

    @api.one
    @api.depends('question_options')
    def calc_options(self):
        self.num_options = self.question_options.search_count([('question_id','=',self.id)])
    
    @api.one
    @api.depends('question_options')
    def calc_correct(self):
        self.num_correct = self.question_options.search_count([('question_id','=',self.id), ('correct','=',True)])
    
class EtqQuestionOptions(models.Model):

    _name = "etq.question.option"
    _rec_name = "option"
    
    question_id = fields.Many2one('etq.question',string="Question ID")
    option = fields.Char(string="Option")
    correct = fields.Boolean(string="Correct")
    
class EtqQuestionOptionBlank(models.Model):

    _name = "etq.question.optionblank"
    
    question_id = fields.Many2one('etq.question',string="Question ID")
    answer = fields.Char(string="Blank Answer")