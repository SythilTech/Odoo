# -*- coding: utf-8 -*-

import requests
from lxml import html

import odoo.http as http
from odoo.http import request
from odoo.exceptions import UserError

class SemSeoToolkitWebsiteController(http.Controller):

    @http.route('/seo/report', type='http', auth="public", website=True)
    def seo_report(self, **kwargs):

        if 'url' in request.params:

            # We don't verify because one of the checks is valid certificate
            try:
                request_response = requests.get(request.params['url'], verify=False)
            except:
                return "Can not access website"

            sem_report = request.env['sem.report.seo'].sudo().create({'url': request.params['url']})

            # Domain level checks
            for seo_check in request.env['sem.check'].sudo().search([('active', '=', True), ('keyword_required', '=', False), ('check_level', '=', 'domain')]):
                method = '_seo_check_%s' % (seo_check.function_name,)
                action = getattr(seo_check, method, None)

                if not action:
                    raise NotImplementedError('Method %r is not implemented' % (method,))

                parsed_html = html.fromstring(request_response.text)

                check_result = action(request_response, parsed_html, False)
                request.env['sem.report.seo.check'].sudo().create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1]})

            # Page level checks
            for seo_check in request.env['sem.check'].sudo().search([('active', '=', True), ('keyword_required', '=', False), ('check_level', '=', 'page')]):
                method = '_seo_check_%s' % (seo_check.function_name,)
                action = getattr(seo_check, method, None)

                if not action:
                    raise NotImplementedError('Method %r is not implemented' % (method,))

                parsed_html = html.fromstring(request_response.text)

                check_result = action(request_response, parsed_html, False)
                request.env['sem.report.seo.check'].sudo().create({'report_id': sem_report.id, 'check_id': seo_check.id, 'check_pass': check_result[0], 'notes': check_result[1]})

            return http.request.render('sem_seo_toolkit_website.seo_report', {'sem_report': sem_report})
        else:
            return http.request.render('sem_seo_toolkit_website.seo_report', {})