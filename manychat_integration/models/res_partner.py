# -*- coding: utf-8 -*-

import requests
import json
import base64

from odoo import api, fields, models

class ResPartnerManyChat(models.Model):

    _inherit = 'res.partner'

    manychat_id = fields.Char(string="ManyChat ID")
    firstname = fields.Char(string="First Name")
    lastname = fields.Char(string="Last Name")

    @api.model
    def manychat_create(self, manychat_page, json_data):

        import_values = {'manychat_id': json_data['data']['id'], 'name': json_data['data']['name'], 'firstname': json_data['data']['first_name'], 'lastname': json_data['data']['last_name']}

        if json_data['data']['is_followup_enabled'] == False:
            import_values['opt_out'] = True

        manychat_custom_fields = []
        for custom_field in json_data['data']['custom_fields']:

            # Try to map the custom field to the Odoo field
            mapping_custom_field = self.env['integration.manychat.map.field'].search([('map_id.im_id', '=', manychat_page.id), ('map_id.model_id.model', '=', 'res.partner'), ('manychat_field_id.name', '=', custom_field['name']), ('odoo_field_id', '!=', False)])
            if mapping_custom_field:
                import_values[mapping_custom_field[0].odoo_field_id.name] = custom_field['value']

        manychat_tags = []
        for tag in json_data['data']['tags']:

            existing_tag = self.env['res.partner.category'].search([('manychat_id','=',tag['id'])])
            if not existing_tag:
                #Create the tag
                existing_tag = self.env['res.partner.category'].create({'manychat_id': tag['id'], 'name': "(ManyChat) " + tag['name']})
            
            manychat_tags.append((4, existing_tag.id))

        import_values['image'] = base64.b64encode(requests.get(json_data['data']['profile_pic']).content)

        import_record = self.env['res.partner'].sudo().create(import_values)

        import_record.category_id = manychat_tags
        
        return import_record

    def manychat_write(self, manychat_page, json_data):

        import_values = {'manychat_id': json_data['data']['id'], 'name': json_data['data']['name'], 'firstname': json_data['data']['first_name'], 'lastname': json_data['data']['last_name']}

        if json_data['data']['is_followup_enabled'] == False:
            import_values['opt_out'] = True

        manychat_custom_fields = []
        for custom_field in json_data['data']['custom_fields']:

            # Try to map the custom field to the Odoo field
            mapping_custom_field = self.env['integration.manychat.map.field'].search([('map_id.im_id', '=', manychat_page.id), ('map_id.model_id.model', '=', 'res.partner'), ('manychat_field_id.name', '=', custom_field['name']), ('odoo_field_id', '!=', False)])
            if mapping_custom_field:
                import_values[mapping_custom_field[0].odoo_field_id.name] = custom_field['value']

        manychat_tags = []
        for tag in json_data['data']['tags']:

            existing_tag = self.env['res.partner.category'].search([('manychat_id','=',tag['id'])])
            if not existing_tag:
                #Create the tag
                existing_tag = self.env['res.partner.category'].create({'manychat_id': tag['id'], 'name': "(ManyChat) " + tag['name']})
            
            manychat_tags.append((4, existing_tag.id))

        import_values['image'] = base64.b64encode(requests.get(json_data['data']['profile_pic']).content)

        self.write(import_values)

        # Remove the existing ManyChat tags and readd the new data (incase tags have been removed from MC)
        for mc_tag in self.category_id:
            if mc_tag.manychat_id:
                self.category_id = [(3, mc_tag.id)]

        self.category_id = manychat_tags