# -*- coding: utf-8 -*-
import json
import requests
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from openerp import api, fields, models

class PaymentMethodSaas(models.Model):

    _inherit = "payment.token"
    
    @api.one
    def charge_card(self, amount, description):
        method = '_charge_token_%s' % (self.acquirer_id.provider,)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	credit_card_charge_response = action(amount, description)
	
    def _charge_token_paypal(self, amount, description):

        #Request access
        base_url = ""
        if self.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        else:
            base_url = "https://api.paypal.com/v1/oauth2/token"

	payload = {'grant_type':"client_credentials"}
	client_id = self.acquirer_id.paypal_client_id
	secret = self.acquirer_id.paypal_secret
	response_string = requests.post(base_url, data=payload, auth=(str(client_id), str(secret)), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept-Language": "en_US"})
        
        json_ob = json.loads(response_string.text)
            
        self.acquirer_id.paypal_api_access_token = json_ob['access_token']
            
        base_url = ""
        if self.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/payments/payment"
        else:
            base_url = "https://api.paypal.com/v1/payments/payment"        
        
        access_token = self.acquirer_id.paypal_api_access_token
        card_partner = self.partner_id
        payload = {
            'intent': 'sale',
            'payer':  {
                "payment_method": "credit_card",
                "funding_instruments": [{
                    "credit_card_token": {
                        "credit_card_id": str(self.acquirer_ref),
                        "payer_id": "res_partner_" + str(card_partner.id)
                    }
                }]
             },
             'transactions': [{
                 'amount':{
                     'total': '{0:.2f}'.format(amount),
                     'currency': str(self.partner_id.company_id.currency_id.name)
                 },
                 'description': description
             }]
        }        
        
        data = json.dumps(payload)
        headers = headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token}
        
        response_string = requests.post(base_url, data=data, headers=headers)
        
        
        _logger.error(response_string.text.encode('utf-8'))
        json_ob = json.loads(response_string.text)
        if 'id' in json_ob:
            type = "server2server"
            state = "done"
            if self.partner_id.country_id:
                partner_country_id = self.partner_id.country_id.id
            else:
                partner_country_id = self.partner_id.company_id.country_id.id
                
            self.env['payment.transaction'].create({'payment_method_id': self.id, 'acquirer_reference': json_ob['id'], 'reference': json_ob['id'], 'partner_id': self.partner_id.id, 'amount': amount, 'type': type, 'state': state,'currency_id': self.partner_id.company_id.currency_id.id, 'acquirer_id': self.acquirer_id.id, 'partner_country_id': partner_country_id, 'state_message': response_string.text, 'date_validate': datetime.utcnow() })
            return json_ob
        else:
            error_string = ""
            
            for paypal_error in json_ob['details']:
                error_string += paypal_error['issue'] + "\n"
            
            _logger.error(error_string)
            raise UserError(error_string)    