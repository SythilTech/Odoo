# -*- coding: utf-8 -*-
import requests
import json
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentMethodTokenWizard(models.TransientModel):

    _name = "payment.method.token.wizard"
    
    payment_method_id = fields.Many2one('payment.method', string="Payment Method")
    number = fields.Char(string="Credit Card Number")
    type = fields.Char(string="Credit Card Type")
    expire_month = fields.Integer(string="Expiry Month")
    expire_year = fields.Integer(string="Expiry Year")
    cvv = fields.Char(string="CVV", help="Card Verification Value")
    
    @api.one
    def fetch_token(self):        
        method = '_generate_token_%s' % (self.payment_method_id.acquirer_id.provider,)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	credit_card_token = action()
	
	self.payment_method_id.acquirer_ref = credit_card_token
	
    def _generate_token_paypal(self):
        _logger.error("Paypal Token")

        #Request access
        base_url = ""
        if self.payment_method_id.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        else:
            base_url = "https://api.paypal.com/v1/oauth2/token"

	payload = {'grant_type':"client_credentials"}
	client_id = self.payment_method_id.acquirer_id.paypal_client_id
	secret = self.payment_method_id.acquirer_id.paypal_secret
	response_string = requests.post(base_url, data=payload, auth=(str(client_id), str(secret)), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept-Language": "en_US"})

        _logger.error(response_string.text)
            
        json_ob = json.loads(response_string.text)
            
        self.payment_method_id.acquirer_id.paypal_api_access_token = json_ob['access_token']
            
        base_url = ""
        if self.payment_method_id.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/vault/credit-cards/"
        else:
            base_url = "https://api.paypal.com/v1/vault/credit-cards/"        
        
        access_token = self.payment_method_id.acquirer_id.paypal_api_access_token
        card_partner = self.payment_method_id.partner_id
        payload = {
            'number': self.number.replace(" ",""),
            'type': self.type,
            'expire_month': self.expire_month,
            'expire_year': self.expire_year,
            'cvv2': self.cvv,
            'first_name': card_partner.name,
            'last_name': card_partner.name,
            'billing_address':  { "line1": card_partner.street, "city": card_partner.city, 'country_code': card_partner.country_id.code, 'postal_code': card_partner.zip, 'state':card_partner.state_id.code, 'phone':card_partner.phone},
            'external_customer_id': self.payment_method_id.partner_id.id
        }
        response_string = requests.post(base_url, data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token})

        _logger.error(response_string.text.encode('utf-8'))
        json_ob = json.loads(response_string.text)
        return json_ob['id']
        
