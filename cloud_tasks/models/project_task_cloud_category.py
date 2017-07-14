# -*- coding: utf-8 -*-
import requests
import logging
_logger = logging.getLogger(__name__)
import json
from openerp import api, fields, models

class ProjectTaskCloudCategory(models.Model):

    _name = "project.task.cloud.category"
    _description = "Cloud Task Category"
    _order = "name asc"
    
    name = fields.Char(string="Name", translate=True)
    
    def test_push_notif(self):
        payload = {'to': "/topics/category_" + str(self.id), 'data':  { "message": "This is a test message"} }        
        response_string = requests.post("https://fcm.googleapis.com/fcm/send", data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "key=" + self.env.user.company_id.firebase_auth_key})
        _logger.error(response_string.text.encode('utf-8'))
    