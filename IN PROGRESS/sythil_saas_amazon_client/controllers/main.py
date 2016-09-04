# -*- coding: utf-8 -*-
import werkzeug
from contextlib import closing
import logging
_logger = logging.getLogger(__name__)
import os
import shutil
import subprocess
from datetime import datetime, timedelta

import openerp
import openerp.http as http
from openerp.http import request
from openerp import SUPERUSER_ID

class SaasAmazonClient(http.Controller):

    @http.route('/saas/client/process', type='http', auth="none")
    def saas_client_amazon(self, **kw):
        return "saas client"