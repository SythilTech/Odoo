# -*- coding: utf-8 -*-

import ast
import json

import odoo.http as http
from odoo.http import Response, request, HttpRequest

class ManyChatIntegrationController(http.Controller):

    @http.route('/manychat/import', type='json', auth="public")
    def manychat_import(self, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        http.request.env['integration.manychat'].sudo().search([('page_id','=', values['page_id'])]).import_subscriber(values['id'])

        return "Import Successful"

    @http.route('/manychat/serve/<slug>', type='http', auth="public", csrf=False)
    def manychat_serve(self, slug, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        manychat_server = http.request.env['integration.manychat.server'].sudo().search([('server_slug', '=', slug)])

        messages = []
        for message in manychat_server.message_ids:
            for record in http.request.env[manychat_server.model_name].sudo().search(ast.literal_eval(manychat_server.domain), limit=10):
                rendered_message_text = http.request.env['integration.manychat.server.message'].sudo().render_message(message.text, manychat_server.model_id.model, record.id)
                messages.append({"type": message.type, "text": rendered_message_text})

        return_json = {"version": "v2",
            "content": {
                "messages": messages
            }
        }
        
        return json.dumps(return_json)