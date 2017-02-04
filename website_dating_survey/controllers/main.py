# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)
import hashlib
import openerp.http as http
from openerp.http import request
from odoo.addons.website.models.website import slug

class WebsiteDatingController(http.Controller):

    @http.route('/dating/survey/<model("res.dating.survey"):survey>', type="http", auth="user", website=True)
    def dating_survey_start(self, survey, **kwargs):
        new_survey_answer = request.env['res.dating.survey.answer'].sudo().create({'survey_id': survey.id, 'partner_id': request.env.user.partner_id.id, 'state': 'incomplete'})
	survey_token = hashlib.md5( str(new_survey_answer.id) ).hexdigest()
	new_survey_answer.survey_token = survey_token
        return werkzeug.utils.redirect("/dating/survey/" + slug(survey) + "/1/" + str(survey_token) )
        
    @http.route('/dating/survey/<model("res.dating.survey"):survey>/<page_number>/<survey_token>', type="http", auth="user", website=True)
    def dating_survey(self, survey, page_number, survey_token, **kwargs):
    
        page = survey.page_ids[ int(page_number) - 1]
                
        return http.request.render('website_dating_survey.dating_survey', {'survey': survey, 'page': page, 'page_number': page_number, 'max_pages': len(survey.page_ids), 'survey_token': survey_token } )

    @http.route('/dating/survey/process', type="http", auth="user", website=True)
    def dating_survey_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
	survey = request.env['res.dating.survey'].sudo().browse( int(values['survey_id']) )
        page = survey.page_ids[ int(values['page_number']) - 1]

	survey_answer = request.env['res.dating.survey.answer'].sudo().search([('survey_token', '=', values['survey_token'] ), ('partner_id', '=', request.env.user.partner_id.id) ])
	
	#Go through each question in this questionnaire
	for question in page.question_ids:
	    #Go through each option and determine if it was selected(prevents submitting options from other questions)
	    for option in question.option_ids:
	        if values["question_" + str(question.id)] == str(option.id):
	            request.env['res.dating.survey.answer.question'].sudo().create({'survey_answer_id': survey_answer.id, 'question_id': question.id, 'option_id': option.id})
	            
	            #Set the value in the member record
	            if question.partner_field_id:
	                survey_answer.partner_id[question.partner_field_id.name] = option.value
	            
	            #Only one option is allowed(prevent multi option injection)
	            break
        
        page_number = int(values['page_number'])
        if page_number == len(survey.page_ids):
            #Go back to home
            survey.state = "complete"
            return werkzeug.utils.redirect("/")
        else:
            #Redirect to next page
            next_page_number = page_number + 1
            return werkzeug.utils.redirect("/dating/survey/" + slug(survey) + "/" +  str(next_page_number) + "/" + str(survey_answer.survey_token) )        