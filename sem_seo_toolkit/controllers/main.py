# -*- coding: utf-8 -*-

import werkzeug
import json
import logging
_logger = logging.getLogger(__name__)

import odoo
from odoo.http import request
import odoo.http as http
from odoo.tools.misc import file_open

class SemSeoTollkitController(http.Controller):

    @http.route('/sem/tracking.js', type='http', auth="public")
    def sem_tracking(self, **kw):
        return http.Response(
                    werkzeug.wsgi.wrap_file(
                        request.httprequest.environ,
                        file_open('sem_seo_toolkit/static/src/js/track.js', 'rb')
                    ),
                    content_type='application/javascript; charset=utf-8',
                )

    @http.route('/sem/track', type='http', auth="public", csrf=False, cors="*")
    def sem_track(self, *kw):
        json_data = json.loads(request.httprequest.data.decode())
        request.env['sem.track'].create({'session_id': json_data['session_id'], 'user_agent': request.httprequest.user_agent, 'start_url': request.httprequest.referrer, 'referrer': json_data['document_referrer'], 'ip': request.httprequest.headers.environ['REMOTE_ADDR']})
        return ""