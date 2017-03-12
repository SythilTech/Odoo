# -*- coding: utf-8 -*-
import requests
import json
import logging
import datetime
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentMethodChargeWizard(models.TransientModel):

    _name = "payment.method.charge.wizard"
    
    payment_method_id = fields.Many2one('payment.method', string="Payment Method")
    amount = fields.Float(string="Amount")
    description = fields.Text(string="Description")

    @api.one
    def charge_card(self):        
        method = '_charge_token_%s' % (self.payment_method_id.acquirer_id.provider,)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	credit_card_charge_response = action()
	
	
    def _charge_token_paypal(self):
        _logger.error("Paypal Charge Token")

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
            
        json_ob = json.loads(response_string.text)
            
        self.payment_method_id.acquirer_id.paypal_api_access_token = json_ob['access_token']
            
        base_url = ""
        if self.payment_method_id.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/payments/payment"
        else:
            base_url = "https://api.paypal.com/v1/payments/payment"        
        
        access_token = self.payment_method_id.acquirer_id.paypal_api_access_token
        card_partner = self.payment_method_id.partner_id
        payload = {
            #'id': str(card_partner.id) + datetime.datetime.now().strftime("%I-%M%p-%B-%d-%Y"),
            'intent': 'sale',
            'payer':  {
                "payment_method": "credit_card",
                "funding_instruments": [{
                    "credit_card_token": {
                        "credit_card_id": str(self.payment_method_id.acquirer_ref),
                        "external_customer_id": str(card_partner.id)
                    }
                }]
             },
             'transactions': [{
                 'amount':{
                     'total': str(self.amount),
                     'currency': str(self.payment_method_id.partner_id.company_id.currency_id.name)
                 },
                 'description': str(self.description)
             }]
        }

        payload = {
            "id":"CPPAY-13U467758H032001PKPIFQZI",
            "intent":"sale",
            "payer":{
                "payment_method":"credit_card",
                "funding_instruments":[
                    {
                        "credit_card_token":{
                            "credit_card_id":"CARD-1MD19612EW4364010KGFNJQI",
                            "external_customer_id":"joe_shopper408-334-8890"
                        }
                    }
                ]
            },
            "transactions":[
                {
                    "amount":{
                        "total":"6.70",
                        "currency":"USD"
                    },
                    "description":"Payment by vaulted credit card."
                }
            ]
        }
        
        _logger.error(payload)
        
        _logger.error(json.dumps(payload))
        
        response_string = requests.post(base_url, data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token})

        _logger.error(response_string.text.encode('utf-8'))
        json_ob = json.loads(response_string.text)
        return json_ob
        
