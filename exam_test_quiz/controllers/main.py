import openerp.http as http
from openerp.http import request, SUPERUSER_ID
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)
import werkzeug
import json

class MyController(http.Controller):

    @http.route('/exam/<exam>', type="http", auth="public", website=True)
    def take_exam(self, exam):
        exam = http.request.env['etq.exam'].sudo().search([('slug','=',exam)])[0]
        return http.request.render('exam_test_quiz.exam_question_page', {'exam': exam})
        
    @http.route('/exam/results', type="http", auth="public", website=True)
    def exam_result(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        exam = http.request.env['etq.exam'].sudo().browse(int(values['ExamID']))
        
        exam_results = ""
        question_count = 0
        correct_count = 0
        
        exam_result = http.request.env['etq.result'].sudo().create({'exam_id':exam.id})
        
        for question in exam.questions:
            question_count += 1
            if question.question_type == 'multi_choice':
            
            
                if question.num_correct > 1:
                    e_result = exam_result.results.sudo().create({'result_id':exam_result.id, 'question':question.id})
                
                    question_result = True
                    for option in question.question_options:
                        fieldy = "question" + str(question.id) + "option" + str(option.id)
                    
                        #They didn't have a checkbox checked for a correct option
                        if option.correct == True and (fieldy in values) == False:
                            question_result = False
                    
                        #They checked the wrong option 
                        if option.correct == False and (fieldy in values) == True:
                            question_result = False
                
                        if fieldy in values == True:
                            http.request.env['etq.result.question.option'].sudo().create({'question_id':e_result.id,'option_id':int(values["question" + str(question.id) + "option" + str(option.id)])})

                    if question_result == True:
                        correct_count += 1
                
                    e_result.correct = question_result
                                
                elif question.num_correct == 1:
                    correct_option = question.question_options.search([('question_id','=',question.id),('correct','=',True)])[0].id
                    question_result = False
                
                    #they choose the correct option     
                    if int(values["question" + str(question.id)]) == int(correct_option):
                        question_result = True
                        correct_count += 1
                    else:
                        question_result = False

                    e_result = exam_result.results.sudo().create({'result_id':exam_result.id, 'question':question.id, 'correct':question_result})
                    http.request.env['etq.result.question.option'].sudo().create({'question_id':e_result.id,'option_id':int(values["question" + str(question.id)])})
            
            
            elif question.question_type == 'fill_blank':
                
                e_result = exam_result.results.sudo().create({'result_id':exam_result.id, 'question':question.id})
                
                question_result = True
                
                option_count = 1
                
                for option in question.question_options_blank:
                    fieldy = "question" + str(question.id) + "option" + str(option_count)
                  
                    if values[fieldy] != option.answer:
                        question_result = False
                    
                    http.request.env['etq.result.question.option'].sudo().create({'question_id':e_result.id, 'option_id':option.id, 'question_options_value': values[fieldy] })
                    
                    option_count += 1
                    
                if question_result == True:
	            correct_count += 1
	                    
                e_result.correct = question_result
        
        percent = float(correct_count) / float(question_count) * 100
        return http.request.render('exam_test_quiz.exam_results', {'exam_result':exam_result, 'question_count': question_count, 'correct_count': correct_count,'percent':percent})