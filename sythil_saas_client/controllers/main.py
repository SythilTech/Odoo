# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime
import werkzeug
import base64
import json
import openerp
from openerp import tools
from openerp.addons.web.controllers.main import ensure_db, db_info
    
class SythilSaasController(openerp.addons.web.controllers.main.Home):
    
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):

        subscription_status = request.env['ir.config_parameter'].sudo().get_param('subscription_status')

        ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        menu_data = request.registry['ir.ui.menu'].load_menus(request.cr, request.uid, request.debug, context=request.context)

        if subscription_status == "trial":
            trial_expiration_date = request.env['ir.config_parameter'].sudo().get_param('trial_expiration_date')        
            trial_expiration_date = datetime.strptime(trial_expiration_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)        
            days_left = abs((trial_expiration_date - datetime.now()).days)
            hours_left = abs((trial_expiration_date - datetime.now()).seconds) / 3600

            if datetime.now() > trial_expiration_date:
                saas_server_url = request.env['ir.config_parameter'].sudo().get_param('saas_server_url')
                
                #Trial has expired so show them a screen to subscribe
                return request.render('sythil_saas_client.saas_trial_expired', {'saas_server_url': saas_server_url})
            else:
                #Show them the web with the trial banner
                return request.render('web.webclient_bootstrap', qcontext={'menu_data': menu_data, 'db_info': json.dumps(db_info()), 'trail_days': days_left, 'trail_hours': hours_left, 'subscription_status': subscription_status})
        elif subscription_status == "canceled":
            return "You have cenceled your subscription and will have to resubscribe to regain access"
        elif subscription_status == "subscribed":
            return request.render('web.webclient_bootstrap', qcontext={'menu_data': menu_data, 'db_info': json.dumps(db_info()), 'subscription_status': subscription_status})

        #Failsafe just show them the regular view        
        return request.render('web.webclient_bootstrap', qcontext={'menu_data': menu_data, 'db_info': json.dumps(db_info()) })        



 
            
