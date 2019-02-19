# -*- coding: utf-8 -*-

import odoo.http as http

class ManyChatIntegrationController(http.Controller):

    @http.route('/manychat/import', type='json', auth="public")
    def manychat_import(self, **kwargs):

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        http.request.env['integration.manychat'].sudo().search([('page_id','=', values['page_id'])]).import_subscriber(values['id'])

        return "Import Successful"