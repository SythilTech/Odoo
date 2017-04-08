from openerp import models, fields, api

import logging
_logger = logging.getLogger(__name__)

import werkzeug
import werkzeug.urls
import random

from openerp import http, SUPERUSER_ID
from openerp.http import request

class eregs(models.Model):

    _inherit = "event.event"

    def default_survey_template(self):
        return self.env['ir.model.data'].get_object('event_registrants_survey', 'event_survey_email')
        
    survey_id = fields.Many2one('survey.survey', string="Survey", domain="[('stage_id','!=','closed')]")
    template_id = fields.Many2one('email.template', string="Survey Email Template", default=default_survey_template, domain="[('model_id.model','=','event.registration')]")
    

    @api.one
    def send_event_survey(self):
    	self.message_post(body="Survey Sent Out", subject="Survey Sent Out")

        for reg in self.registration_ids.search([('state','=','done')]):
            
            values = self.env['email.template'].generate_email(self.template_id.id, reg.id)
            values['email_to'] = reg.email
	    msg_id = self.env['mail.mail'].create(values)
	    self.env['mail.mail'].send([msg_id], True)
	    