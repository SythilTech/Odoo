# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)
import werkzeug.utils
import werkzeug.wrappers
import urllib2

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class VoipController(http.Controller):

    @http.route('/voip/window', type="http", auth="user")
    def voip_window(self, **kwargs):
        """Window for video calls which can be dragged around"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        voip_room = request.env['voip.room'].browse( int(values['room']) )
        to_partner = voip_room.partner_ids[1]
        return http.request.render('voip_sip_webrtc.voip_window', {'voip_room':voip_room, 'to_partner': to_partner})
        
    @http.route('/voip/call/begin', type="http", auth="user")
    def voip_call_begin(self, **kwargs):
        """Call starts after a person accepts access to camera"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        to_partner = request.env['res.partner'].browse( int(values['to_partner']) )
        call_id = request.env['voip.call'].create({'status': 'pending', 'partner_id': to_partner.id})
        
        return json.dumps({'call_id': call_id.id})
        
    @http.route('/voip/call/end', type="http", auth="user")
    def voip_call_end(self, **kwargs):
        """Call ends when person clicks the the end call button"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        call = request.env['voip.call'].browse( int(values['call_id']) )
        call.status = 'over'
        call.end_time = datetime.datetime.now()
        diff_time = datetime.datetime.strptime(call.end_time, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(call.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
        call.duration = str(diff_time.seconds) + " Seconds"
        return True