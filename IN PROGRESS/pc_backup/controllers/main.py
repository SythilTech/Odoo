# -*- coding: utf-8 -*-
import werkzeug
import json
import base64

import openerp.http as http
from openerp.http import request

from openerp.addons.website.models.website import slug

class BackupController(http.Controller):

    @http.route('/backup/client/download', type="http", auth="user")
    def backup_client_download(self, **kw):
        """Displays all help groups and thier child help pages"""
        return http.request.render('pc_backup.download_client', {})