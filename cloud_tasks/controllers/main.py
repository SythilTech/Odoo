# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
import openerp
import tempfile
import zipfile
import os
import requests
import string
import random
import ntpath
import hashlib

import openerp.http as http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

from openerp.addons.website.models.website import slug

class CloudTasksController(http.Controller):

    @http.route('/cloud/task/download', type="http", auth="public")
    def cloud_task_download(self, **kwargs):

        headers = [
            ('Content-Type', 'application/octet-stream; charset=binary'),
            ('Content-Disposition', "attachment; filename=CloudTasks.apk" ),
        ]

        module_directory = openerp.modules.get_module_path("cloud_tasks")            
        apk_file = module_directory + "/android/build/outputs/apk/app-debug.apk"
        
        response = werkzeug.wrappers.Response(file(apk_file), headers=headers, direct_passthrough=True)
        return response

    @http.route('/cloud/task/create', type="http", auth="public")
    def cloud_task_create(self, **kwargs):
        """Handle the creation of the task server side for security"""

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        _logger.error("Create Cloud Task")
        task_category = request.env['project.task.cloud.category'].sudo().search([('name','=',values['category'])])[0]
        new_task = request.env['project.task'].sudo().create({'cloud_task':True, 'cloud_task_category': task_category.id, 'name': values['name'], 'description': values['description'], 'user_id': ''})

        my_return = []

        payload = {'to': "/topics/category_" + str(task_category.id), 'data':  { "message": "A new task has been created in the category " + task_category.name} }
        
        response_string = requests.post("https://fcm.googleapis.com/fcm/send", data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "key=" + request.env.user.company_id.firebase_auth_key})

        _logger.error(response_string.text.encode('utf-8'))
                        
        return "Task has been created"

    @http.route('/cloud/task/categories', type="http", auth="public")
    def cloud_task_categories(self, **kwargs):
        """Returns a json list of cloud task categoriescategories"""

        _logger.error("Get Cloud Categories")

        my_return = []
                
        for category in request.env['project.task.cloud.category'].sudo().search([]):
            return_item = {"id": category.id, "name": category.name}
            my_return.append(return_item) 
        
        return json.JSONEncoder().encode(my_return)
