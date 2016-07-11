# -*- coding: utf-8 -*-
import werkzeug
import json
import base64

import openerp.http as http
from openerp.http import request

from openerp.addons.website.models.website import slug

import logging
_logger = logging.getLogger(__name__)

class MassImageUploadController(http.Controller):

    @http.route('/mass/image/upload', type="http", auth="user")
    def mass_image_upload(self, **kw):
        """Simple UI to upload the images"""
        return http.request.render('mass_image_upload.mass_upload_page', {})

    @http.route('/mass/image/upload/file',auth="user", website=True, type="json", csrf=False)
    def mass_image_upload_file(self, base64string, fileName, mapField):
        """Upload a single file and send back an error of success"""

        filename = fileName.split(".")[0]
        
        #Find the record those field matches the filename
        my_record = request.env['res.partner'].search([(mapField,'=',filename)])

        if len(my_record) == 0:
            status = "error"
            message = filename + " could not be mapped to a record"        
        elif len(my_record) == 1:
        
            my_record.image = base64string
            status = "success"
            message = filename + " has been uploaded successful to record " + str(my_record.name)
        else:
            status = "error"
            message = filename + " matched more then one record"

        return {"status": status,"message": message}