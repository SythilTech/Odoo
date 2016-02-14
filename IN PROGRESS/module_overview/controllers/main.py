# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

class ModuleOverView(http.Controller):

    @http.route('/module/overview', type="http", auth="public", website=True)
    def module_picker(self, **kwargs):
        """Gives an overview of what is inside a module"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        #module_url = "https://apps.openerp.com/apps/modules/" + values['version'] + "/" + values['name']
        
        return http.request.render('module_overview.pick_module', {})