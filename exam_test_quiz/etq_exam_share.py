from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
from datetime import datetime
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import unicodedata
import re

class etq_exam_share(models.Model):

    _name = "etq.exam.share"
    
    exam_id = fields.Many2one('etq.exam', string="Exam")
    share_type = fields.Selection((('existing_contacts','Existing Contacts'),('new_contacts','New Contacts')), string="Share Option", required=True, default="existing_contacts")
    partner_ids = fields.Many2many('res.partner', string="Existing Contacts")
    email_list = fields.Text(string="Email List", placeholder="Comma seperated emails")
    email_subject = fields.Char(string="Email Subject", required=True)
    email_content = fields.Html(string="Email Content", required=True, sanizied=False)
    
    @api.onchange('exam_id')
    def _change_share(self):
        notification_template = self.env['ir.model.data'].get_object('exam_test_quiz', 'exam_share_email')
	
        self.email_subject = notification_template.subject
        
        temp_content = notification_template.body_html
	temp_content = temp_content.replace('__URL__',request.httprequest.host_url + "exam/" + self.exam_id.slug)
	temp_content = temp_content.replace('__EXAM__',self.exam_id.name)
        
        self.email_content = temp_content	             
        
        request.httprequest.host_url + "form/myinsert"
        
    @api.one
    def share_exam(self):
        notification_template = self.env['ir.model.data'].get_object('exam_test_quiz', 'exam_share_email')        

        for cust in self.partner_ids:
            notification_template.subject = self.email_subject
            notification_template.body_html = self.email_content
            notification_template.send_mail(cust.id, True)