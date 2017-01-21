import openerp.http as http
import openerp
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class HtmlFormControllerActionEmail(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    def _html_action_send_email(self, submit_action, history_data, values):
        html_body = ""
        html_body += "<h1>" + history_data.html_id.name + " Form Data</h1>\n"
        for insert_data in history_data.insert_data:
            html_body += "<b>" + insert_data.field_id.field_description.encode("utf-8") + "</b><br/>\n"
            html_body += insert_data.insert_value + "<br/>\n"
            html_body += "<br/>\n"
        
        html_body += "record link: <a href=\"" + request.httprequest.host_url + "web?id=" + str(history_data.record_id) + "&view_type=form&model=" + str(history_data.html_id.model_id.model) + "#id=" + str(history_data.record_id) + "&view_type=form&model=" + str(history_data.html_id.model_id.model) + "\">record</a>"
        
        my_mail = request.env['mail.mail'].sudo().create({'auto_delete': False, 'email_from': submit_action.from_email, 'email_to': submit_action.to_email, 'subject': history_data.html_id.name + " Form Data", 'body_html': html_body})
                
        if "html_form_mail_attachment" in values:
            file = values['html_form_mail_attachment']
            my_attachment = request.env['ir.attachment'].sudo().create({'name': file.filename, 'datas_fname': file.filename, 'datas': base64.encodestring( file.read() ), 'res_model': 'mail.mail', 'res_id': my_mail.id })
            my_mail.attachment_ids = [(4, my_attachment.id)]
            my_mail.auto_delete = True
        
        