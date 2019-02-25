# -*- coding: utf-8 -*-

import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models

class IntegrationManyChat(models.Model):

    _name = 'integration.manychat'

    name = fields.Char(string="Account Name", help="Human meaningful name to describe the account", required=True)
    authorization_token = fields.Char(string="Authorization Token", help="ManyChat->Settings->API->Get Token", required=True)
    page_id = fields.Char(string="Page ID", compute="_compute_page_id", store=True)
    import_model_id = fields.Many2one('ir.model', string="Import Model", help="Which model the subscriber will get imported into")
    record_link_ids = fields.One2many('integration.manychat.map', 'im_id', string="Record Links")
    field_ids = fields.One2many('integration.manychat.field', 'im_id', string="Custom Fields")
    tag_ids = fields.One2many('integration.manychat.tag', 'im_id', string="Tags")
    subscriber_ids = fields.One2many('integration.manychat.subscriber', 'im_id', string="Subscribers")

    @api.depends('authorization_token')
    def _compute_page_id(self):
        if ":" in self.authorization_token:
            self.page_id = self.authorization_token.split(":")[0]

    def import_custom_data(self):

        # Import the custom fields from ManyChat
        response_string = requests.get("https://api.manychat.com/fb/page/getCustomFields", headers={"Authorization":"Bearer " + self.authorization_token})
        json_data = json.loads(response_string.text)
        for custom_field in json_data['data']:
            #Don't reimport the same field
            if self.env['integration.manychat.field'].search_count([('im_id', '=', self.id), ('manychat_id', '=', custom_field['id'])]) == 0:
                self.env['integration.manychat.field'].sudo().create({'im_id': self.id, 'manychat_id': custom_field['id'], 'name': custom_field['name'], 'type': custom_field['type'], 'description': custom_field['description']})

        # Import the tags from ManyChat
        response_string = requests.get("https://api.manychat.com/fb/page/getTags", headers={"Authorization":"Bearer " + self.authorization_token})
        json_data = json.loads(response_string.text)
        for tag in json_data['data']:
            #Don't reimport the same tag
            if self.env['integration.manychat.tag'].search_count([('im_id', '=', self.id), ('manychat_id', '=', tag['id'])]) == 0:
                self.env['integration.manychat.tag'].sudo().create({'im_id': self.id, 'manychat_id': tag['id'], 'name': tag['name']})

    @api.multi
    def import_individual_subscriber(self):
        self.ensure_one()

        return {
            'name': 'Import Individual Subscriber',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'integration.manychat.import',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_im_id': self.id}
         }

    def import_subscriber(self, subscriber_id):
        url = "https://api.manychat.com/fb/subscriber/getInfo?subscriber_id=" + str(subscriber_id)
        response_string = requests.get(url, headers={"Authorization":"Bearer " + self.authorization_token})
        json_data = json.loads(response_string.text)

        import_values = {}
        import_values['im_id'] = self.id
        import_values['manychat_id'] = json_data['data']['id']
        import_values['page_id'] = json_data['data']['page_id']

        user_refs = []
        for user_ref in json_data['data']['user_refs']:
            user_refs.append((0,0, {'user_ref': user_ref['user_ref'], 'opted_in': user_ref['opted_in']}))

        import_values['user_ref_ids'] = user_refs

        import_values['status'] = json_data['data']['status']
        import_values['first_name'] = json_data['data']['first_name']
        import_values['last_name'] = json_data['data']['last_name']
        import_values['name'] = json_data['data']['name']
        import_values['gender'] = json_data['data']['gender']
        import_values['profile_pic'] = base64.b64encode(requests.get(json_data['data']['profile_pic']).content)
        import_values['locale'] = json_data['data']['locale']
        import_values['language'] = json_data['data']['language']
        import_values['timezone'] = json_data['data']['timezone']
        import_values['live_chat_url'] = json_data['data']['live_chat_url']
        import_values['last_input_text'] = json_data['data']['last_input_text']
        import_values['subscribed'] = json_data['data']['subscribed']
        import_values['last_interaction'] = json_data['data']['last_interaction']
        import_values['last_seen'] = json_data['data']['last_seen']
        import_values['is_followup_enabled'] = json_data['data']['is_followup_enabled']

        manychat_custom_fields = []
        for custom_field in json_data['data']['custom_fields']:
            existing_custom_field = self.env['integration.manychat.field'].search([('im_id', '=', self.id), ('manychat_id', '=', custom_field['id'])])
            if existing_custom_field:
                manychat_custom_fields.append((0,0, {'imf_id': existing_custom_field.id, 'value': custom_field['value']}))

        import_values['custom_field_ids'] = manychat_custom_fields

        manychat_custom_tags = []
        for custom_tag in json_data['data']['tags']:
            existing_custom_tag = self.env['integration.manychat.tag'].search([('im_id', '=', self.id), ('manychat_id', '=', custom_tag['id'])])
            if existing_custom_tag:
                manychat_custom_tags.append(existing_custom_tag.id)

        import_values['tag_ids'] = [(6,0, manychat_custom_tags)]

        #Don't recreate the same subscriber / record
        import_record = self.env['integration.manychat.subscriber'].search([('manychat_id', '=', json_data['data']['id'])])
        if import_record:
            for user_ref in import_record.sudo().user_ref_ids:
                user_ref.unlink()
            for custom_field in import_record.sudo().custom_field_ids:
                custom_field.unlink()
            import_record.sudo().write(import_values)

            # Transfer data to linked records if they still exists
            for record_link in import_record.record_link_ids:
                linked_record = self.env[record_link.record_model_id.model].browse(record_link.record_id)
                if linked_record:
                    linked_record.manychat_write(self, json_data)
        else:
            import_record = self.env['integration.manychat.subscriber'].sudo().create(import_values)

        # Check if a record already exists for the import model
        if self.import_model_id:
            if self.env['integration.manychat.subscriber.link'].search_count([('sub_id', '=', import_record.id), ('record_model_id', '=', self.import_model_id.id)]) == 0:
                new_record = self.env[self.import_model_id.model].manychat_create(self, json_data)

                # Create a link to the record so we can update it later
                import_record.record_link_ids = [(0,0,{'sub_id': import_record.id, 'record_model_id': self.import_model_id.id, 'record_id': new_record.id})]

    def update_subscriber_data(self):
        for subscriber in self.subscriber_ids:
            self.import_subscriber(subscriber.manychat_id)

class IntegrationManyChatimport(models.TransientModel):

    _name = 'integration.manychat.import'

    im_id = fields.Many2one('integration.manychat', string="ManyChat Account")
    subscriber_id = fields.Char(string="Subscriber ID", required=True)

    @api.multi
    def wizard_import_subscriber(self):
        self.ensure_one()

        new_record = self.im_id.import_subscriber(self.subscriber_id)

class IntegrationManyChatMap(models.Model):

    _name = 'integration.manychat.map'

    im_id = fields.Many2one('integration.manychat', string="ManyChat Page")
    model_id = fields.Many2one('ir.model', string="Model", required="True")
    field_map_ids = fields.One2many('integration.manychat.map.field', 'map_id', string="Field Mapping")

class IntegrationManyChatMapField(models.Model):

    _name = 'integration.manychat.map.field'

    map_id = fields.Many2one('integration.manychat.map', string="ManyChat Record Link")
    model_id = fields.Many2one('ir.model', string="Model")
    manychat_field_id = fields.Many2one('integration.manychat.field', string="ManyChat Field")
    odoo_field_id = fields.Many2one('ir.model.fields', string="Odoo Field")

    @api.multi
    def name_get(self):
        res = []
        for map in self:
            res.append((map.id, map.manychat_field_id.name + " -> " + map.odoo_field_id.name))
        return res

class IntegrationManyChatField(models.Model):

    _name = 'integration.manychat.field'

    im_id = fields.Many2one('integration.manychat', string="ManyChat Account")
    manychat_id = fields.Char(string="ManyChat ID")
    name = fields.Char(string="Name")
    type = fields.Char(string="Type")
    description = fields.Char(string="Description")

class IntegrationManyChatTag(models.Model):

    _name = 'integration.manychat.tag'

    im_id = fields.Many2one('integration.manychat', string="ManyChat Account")
    manychat_id = fields.Char(string="ManyChat ID")
    name = fields.Char(string="Name")

class IntegrationManyChatSubscriber(models.Model):

    _name = 'integration.manychat.subscriber'

    im_id = fields.Many2one('integration.manychat', string="ManyChat Account")
    manychat_id = fields.Char(string="ManyChat ID")
    page_id = fields.Char(string="Page ID")
    user_ref_ids = fields.One2many('integration.manychat.subscriber.ref', 'sub_id', string="User Refs")
    status = fields.Boolean(string="Status")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    name = fields.Char(string="Name")
    gender = fields.Char(string="Gender")
    profile_pic = fields.Binary(string="Profile Pic")
    locale = fields.Char(string="Locale")
    language = fields.Char(string="Language")
    timezone = fields.Char(string="Timezone")
    live_chat_url = fields.Char(string="Live Chat URL")
    last_input_text = fields.Text(string="Last Input Text")
    subscribed = fields.Datetime(string="Subscribed")
    last_interaction = fields.Datetime(string="Last Interaction")
    last_seen = fields.Datetime(string="Last Seen")
    is_followup_enabled = fields.Boolean(string="Is Followup Enabled")
    custom_field_ids = fields.One2many('integration.manychat.subscriber.field', 'sub_id', string="Custom Fields")
    tag_ids = fields.Many2many('integration.manychat.tag', string="Tags")
    record_link_ids = fields.One2many('integration.manychat.subscriber.link', 'sub_id', string="Record Links")

    @api.multi
    def create_record_link(self):
        self.ensure_one()

        # Remove existing candiates from previous search
        for candidate in self.env['i.m.s.l.candidate.wizard'].search([]):
            candidate.unlink()

        # Go through each custom field for the subscriber and check if there is a mapping rule
        for subscriber_custom_field in self.custom_field_ids:
            # Find any mapping rules for this field for this account
            for mapping_field_rule in self.env['integration.manychat.map.field'].search([('map_id.im_id', '=', self.im_id.id), ('manychat_field_id', '=', subscriber_custom_field.imf_id.id)]):
                # Search through the model for a record that matches the custom field data e.g. Manychat Custom Field 'email' = crm.lead email_from
                found_records = self.env[mapping_field_rule.map_id.model_id.model].sudo().search([(mapping_field_rule.odoo_field_id.name, '=', subscriber_custom_field.value)])
                for found_record in found_records:
                    # Create them so the end user can select which record to link to the subscriber
                    self.env['i.m.s.l.candidate.wizard'].create({'record_model_id': mapping_field_rule.map_id.model_id.id, 'record_id': found_record.id, 'field_link_id': mapping_field_rule.id})

        return {
            'name': 'Create Record LInk',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'i.m.s.l.w',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_sub_id': self.id}
         }

class IntegrationManyChatSubscriberLinkWizard(models.TransientModel):

    _name = 'i.m.s.l.w'

    sub_id = fields.Many2one('integration.manychat.subscriber', string="Subscriber")
    candidate_record_ids = fields.Many2many('i.m.s.l.candidate.wizard', string="Candidate Records")

    def create_links(self):
        for rec in self.candidate_record_ids:
            self.env['integration.manychat.subscriber.link'].create({'sub_id': self.sub_id.id, 'record_model_id': rec.record_model_id.id, 'record_id': rec.record_id})

class IntegrationManyChatSubscriberLinkCandidatekWizard(models.Model):

    _name = 'i.m.s.l.candidate.wizard'

    record_model_id = fields.Many2one('ir.model', string="Record Model")
    record_id = fields.Integer(string="Record ID")
    record_name = fields.Char(string="Record Name", compute="_compute_record_name")
    field_link_id = fields.Many2one('integration.manychat.map.field', string="Field Link")

    @api.one
    @api.depends('record_model_id', 'record_id')
    def _compute_record_name(self):
        self.record_name = self.env[self.record_model_id.model].browse(self.record_id).name_get()[0][1]

class IntegrationManyChatSubscriberLink(models.Model):

    _name = 'integration.manychat.subscriber.link'

    sub_id = fields.Many2one('integration.manychat.subscriber', string="Subscriber")
    record_model_id = fields.Many2one('ir.model', string="Record Model")
    record_id = fields.Integer(string="Record ID")

class IntegrationManyChatSubscriberRef(models.Model):

    _name = 'integration.manychat.subscriber.ref'

    sub_id = fields.Many2one('integration.manychat.subscriber', string="ManyChat Subscriber")
    user_ref = fields.Char(string="User Ref")
    opted_in = fields.Datetime(string="Opted In")

class IntegrationManyChatSubscriberField(models.Model):

    _name = 'integration.manychat.subscriber.field'

    sub_id = fields.Many2one('integration.manychat.subscriber', string="ManyChat Subscriber")
    imf_id = fields.Many2one('integration.manychat.field', string="ManyChat Field")
    value = fields.Char(String="Value")