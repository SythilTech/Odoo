# -*- coding: utf-8 -*-
from openerp.http import request
import requests
import logging
import base64
_logger = logging.getLogger(__name__)
import json

from openerp import api, fields, models

class HtmlFormActionMailchimp(models.Model):

    _inherit = "html.form.action"
    
    mailchimp_api_key = fields.Char(string="API Key")
    mailchimp_list_id = fields.Many2one('html.form.action.mailchimplist', string="Mailchimp List")
    status = fields.Selection([('pending',' Pending'), ('subscribed','Subscribed')], string="Subscription Status", help="pending means send confirmation mail", default="subscribed")
    
    @api.onchange('mailchimp_api_key')
    def _onchange_mailchimp_api_key(self):
        if self.mailchimp_api_key:
            _logger.error("Mailchimp API Change")

            payload = {'user': 'anystring:' + self.mailchimp_api_key}
            code = self.mailchimp_api_key.split("-")[1]

            response_string = requests.get("https://" + str(code) + ".api.mailchimp.com/3.0/lists", params=payload, headers={"Content-Type": "application/json", "Authorization": "Basic " + base64.b64encode( 'user:' + self.mailchimp_api_key )})
            
            json_lists = json.loads(response_string.text)
            
            for json_list in json_lists['lists']:
                
                list_number = json_list['id']
                list_name = json_list['name']
                
                #Add it to the list if it is new
                if self.env['html.form.action.mailchimplist'].sudo().search_count([('list_number','=', list_number)]) == 0:
                    self.env['html.form.action.mailchimplist'].sudo().create({'list_number': list_number, 'name': list_name})


    @api.onchange('mailchimp_list_id')
    def _onchange_mailchimp_list_id(self):
        if self.mailchimp_list_id:
            self.settings_description = "API: " + self.mailchimp_api_key.encode("UTF-8") + ", List: " + self.mailchimp_list_id.name.encode("UTF-8")

class HtmlFormActionMailchimpList(models.Model):

    _name = "html.form.action.mailchimplist"

    name = fields.Char(string="Name")
    list_number = fields.Char(string="List ID")