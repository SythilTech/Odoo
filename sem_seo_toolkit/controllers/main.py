# -*- coding: utf-8 -*-

import odoo.http as http

class GoogleAdsAuthController(http.Controller):

    @http.route('/google/ads/auth', website=True, type='http', auth="public")
    def google_ads_auth(self, **kw):
        return "Hi"
        #return werkzeug.utils.redirect("/web")