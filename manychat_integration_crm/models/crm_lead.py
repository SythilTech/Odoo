# -*- coding: utf-8 -*-

import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models

class CrmLeadManyChat(models.Model):

    _inherit = 'crm.lead'

    manychat_id = fields.Char(string="ManyChat ID")
    contact_firstname = fields.Char(string="Contact Firstname")
    contact_lastname = fields.Char(string="Contact Lastname")
    image = fields.Binary(string="Image")
    manychat_custom_field_ids = fields.Char()
    live_chat_url = fields.Char(string="Live Chat URL")

    @api.model
    def manychat_create(self, manychat_page, json_data):

        import_values = {'manychat_id': json_data['data']['id'], 'name': json_data['data']['name'], 'contact_name': json_data['data']['name'], 'contact_firstname': json_data['data']['first_name'], 'contact_lastname': json_data['data']['last_name'], 'live_chat_url': json_data['data']['live_chat_url']}

        if json_data['data']['is_followup_enabled'] == False:
            import_values['opt_out'] = True

        manychat_custom_fields = []
        for custom_field in json_data['data']['custom_fields']:

            # Try to map the custom field to the Odoo field
            mapping_custom_field = self.env['integration.manychat.map.field'].search([('map_id.im_id', '=', manychat_page.id), ('map_id.model_id.model', '=', 'crm.lead'), ('manychat_field_id.name', '=', custom_field['name']), ('odoo_field_id', '!=', False)])
            if mapping_custom_field:
                if mapping_custom_field[0].odoo_field_id.ttype == "many2one":
                    import_values[mapping_custom_field[0].odoo_field_id.name] = int(custom_field['value'])
                else:
                    import_values[mapping_custom_field[0].odoo_field_id.name] = custom_field['value']

        manychat_tags = []
        for tag in json_data['data']['tags']:

            existing_tag = self.env['crm.lead.tag'].sudo().search([('manychat_id','=',tag['id'])])
            if not existing_tag:
                #Create the tag
                existing_tag = self.env['crm.lead.tag'].sudo().create({'manychat_id': tag['id'], 'name': "(ManyChat) " + tag['name']})
            
            manychat_tags.append((4, existing_tag.id))

        import_values['image'] = base64.b64encode(requests.get(json_data['data']['profile_pic']).content)

        import_record = self.env['crm.lead'].sudo().create(import_values)

        import_record.tag_ids = manychat_tags

        return import_record

    def manychat_write(self, manychat_page, json_data):

        import_values = {'manychat_id': json_data['data']['id'], 'name': json_data['data']['name'], 'contact_name': json_data['data']['name'], 'contact_firstname': json_data['data']['first_name'], 'contact_lastname': json_data['data']['last_name'], 'live_chat_url': json_data['data']['live_chat_url']}

        if json_data['data']['is_followup_enabled'] == False:
            import_values['opt_out'] = True

        manychat_custom_fields = []
        for custom_field in json_data['data']['custom_fields']:
            _logger.error(custom_field['name'])
            # Try to map the custom field to the Odoo field
            mapping_custom_field = self.env['integration.manychat.map.field'].search([('map_id.im_id', '=', manychat_page.id), ('map_id.model_id.model', '=', 'crm.lead'), ('manychat_field_id.name', '=', custom_field['name']), ('odoo_field_id', '!=', False)])
            if mapping_custom_field:
                if mapping_custom_field[0].odoo_field_id.ttype == "many2one":
                    import_values[mapping_custom_field[0].odoo_field_id.name] = int(custom_field['value'])
                else:
                    import_values[mapping_custom_field[0].odoo_field_id.name] = custom_field['value']

        manychat_tags = []
        for tag in json_data['data']['tags']:

            existing_tag = self.env['crm.lead.tag'].sudo().search([('manychat_id','=',tag['id'])])
            if not existing_tag:
                #Create the tag
                existing_tag = self.env['crm.lead.tag'].sudo().create({'manychat_id': tag['id'], 'name': "(ManyChat) " + tag['name']})
            
            manychat_tags.append((4, existing_tag.id))

        import_values['image'] = base64.b64encode(requests.get(json_data['data']['profile_pic']).content)

        self.write(import_values)

        self.tag_ids = manychat_tags