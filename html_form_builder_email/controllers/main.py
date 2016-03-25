import openerp.http as http
import openerp
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class HtmlFormControllerActionEmail(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    def _html_action_send_email(self, submit_action, history_data):
        html_body = ""
        html_body += "<h1>" + history_data.html_id.name + " Form Data</h1>\n"
        for insert_data in history_data.insert_data:
            html_body += "<b>" + insert_data.field_id.field_description.encode("utf-8") + "</b><br/>\n"
            html_body += insert_data.insert_value + "<br/>\n"
            html_body += "<br/>\n"
        
        my_mail = request.env['mail.mail'].sudo().create({'auto_delete': False, 'email_from': submit_action.from_email, 'email_to': submit_action.to_email, 'subject': history_data.html_id.name + " Form Data", 'body_html': html_body})
        my_mail.send()