# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
import os
import shutil
import subprocess
from datetime import datetime, timedelta
import json
import urllib2
import requests
import zipfile
import StringIO
import base64
import tempfile
import odoo

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasDomainController(http.Controller):

    @http.route('/saas/domain/test', type='http', auth="none")
    def saas_client_domain_test(self, **kw):
        saas_server_db = odoo.tools.config['sythilsaasserver']
        return "SAAS Database: " + str(saas_server_db)