# -*- coding: utf-8 -*-
import werkzeug
from datetime import datetime
import json
import math

import openerp.http as http
from openerp.http import request

class WebsiteDatingEventsController(http.Controller):

    @http.route('/dating/events', type="http", auth="public", website=True)
    def dating_events(self, **kwargs):
        
        events = request.env['event.event'].search([('dating_event','=',True)])
        
        return http.request.render('website_dating_events.event_list', {'events': events} )