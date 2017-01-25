import openerp.http as http
import openerp
from openerp.http import request
import requests
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class HtmlFormControllerActionMailchimp(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    def _html_action_mailchimp(self, submit_action, history_data, values):
        
        payload = {'email_address': values['email'], 'status': submit_action.status, 'merge_fields':  { "FNAME": values['contact_firstname'], "LNAME": values['contact_lastname']} }
        code = submit_action.mailchimp_api_key.split("-")[1]
        
        response_string = requests.post("https://" + str(code) + ".api.mailchimp.com/3.0/lists/" + submit_action.mailchimp_list_id.list_number + "/members", data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "Basic " + base64.b64encode( 'user:' + submit_action.mailchimp_api_key )})
        _logger.error(response_string.text)