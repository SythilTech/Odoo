# -*- coding: utf-8 -*-
import requests
import json
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentMethodTokenWizard(models.TransientModel):

    _name = "payment.method.token.wizard"
    
    name = fields.Char(string="Name", help="Human meaningful reference for when the partner has multiple credit cards and wants to charge a particular one")
    partner_id = fields.Many2one('res.partner', string="Partner", required="True")
    acquirer_id = fields.Many2one('payment.acquirer', string="Payment Acquirer", domain="[('provider','!=','transfer')]", required="True")
    number = fields.Char(string="Credit Card Number", required="True")
    type = fields.Char(string="Credit Card Type", required="True")
    expire_month = fields.Char(string="Expiry Month", required="True")
    expire_year = fields.Char(string="Expiry Year", required="True")
    cvv = fields.Char(string="CVV", help="Card Verification Value", required="True")
    
    @api.multi
    def fetch_token(self):
        self.ensure_one()
        method = '_generate_token_%s' % (self.acquirer_id.provider,)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	credit_card_token = action()
	
	new_payment_method = self.env['payment.method'].create({'name': self.name, 'partner_id': self.partner_id.id, 'acquirer_id': self.acquirer_id.id, 'acquirer_ref': credit_card_token})
		
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payment.method',
            'res_id': new_payment_method.id,
        }
        
    def _generate_token_paypal(self):

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
            base_url = "https://api.sandbox.paypal.com/v1/vault/credit-cards/"
        else:
            base_url = "https://api.paypal.com/v1/vault/credit-cards/"        
        
        access_token = self.acquirer_id.paypal_api_access_token
        card_partner = self.partner_id
        payload = {
            'number': self.number.replace(" ",""),
            'type': self.type,
            'expire_month': self.expire_month,
            'expire_year': self.expire_year,
            'cvv2': self.cvv,
            'first_name': card_partner.name,
            'last_name': card_partner.name,
            'billing_address':  { "line1": card_partner.street, "city": card_partner.city, 'country_code': card_partner.country_id.code, 'postal_code': card_partner.zip, 'state':card_partner.state_id.code, 'phone':card_partner.phone},
            'external_customer_id': "res_partner_" + str(self.partner_id.id)
        }
        
        response_string = requests.post(base_url, data=json.dumps(payload), headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token})

        json_ob = json.loads(response_string.text)
        
        if 'id' in json_ob:
            return json_ob['id']
        else:
            error_string = ""
            
            for paypal_error in json_ob['details']:
                error_string += paypal_error['issue'] + "\n"
            
            raise UserError(error_string)