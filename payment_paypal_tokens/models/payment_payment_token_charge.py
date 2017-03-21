# -*- coding: utf-8 -*-
import requests
import json
from openerp.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

from openerp import api, fields, models

class PaymentPaymentTokenCharge(models.Model):

    _inherit = "account.payment"
    
    token_card_id = fields.Many2one('payment.method', string="Credit Card", required="True")
        
    @api.one
    def charge_card(self):
        method = '_charge_token_%s' % (self.token_card_id.acquirer_id.provider,)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	credit_card_charge_response = action()	

        if self.state != 'draft':
            raise UserError(_("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

        if any(inv.state != 'open' for inv in self.invoice_ids):
            raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

        # Use the right sequence to set the name
        if self.payment_type == 'transfer':
            sequence_code = 'account.payment.transfer'
        else:
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    sequence_code = 'account.payment.customer.invoice'
                if self.payment_type == 'outbound':
                    sequence_code = 'account.payment.customer.refund'
            if self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    sequence_code = 'account.payment.supplier.refund'
                if self.payment_type == 'outbound':
                    sequence_code = 'account.payment.supplier.invoice'
        self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(sequence_code)

        # Create the journal entry
        amount = self.amount * (self.payment_type in ('outbound', 'transfer') and 1 or -1)
        move = self._create_payment_entry(amount)

        # In case of a transfer, the first journal entry created debited the source liquidity account and credited
        # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
        if self.payment_type == 'transfer':
            transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == self.company_id.transfer_account_id)
            transfer_debit_aml = self._create_transfer_entry(amount)
            (transfer_credit_aml + transfer_debit_aml).reconcile()

        self.state = 'posted'
	
    def _charge_token_paypal(self):

        #Request access
        base_url = ""
        if self.token_card_id.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        else:
            base_url = "https://api.paypal.com/v1/oauth2/token"

	payload = {'grant_type':"client_credentials"}
	client_id = self.token_card_id.acquirer_id.paypal_client_id
	secret = self.token_card_id.acquirer_id.paypal_secret
	response_string = requests.post(base_url, data=payload, auth=(str(client_id), str(secret)), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept-Language": "en_US"})
        
        json_ob = json.loads(response_string.text)
            
        self.token_card_id.acquirer_id.paypal_api_access_token = json_ob['access_token']
            
        base_url = ""
        if self.token_card_id.acquirer_id.environment == "test":
            base_url = "https://api.sandbox.paypal.com/v1/payments/payment"
        else:
            base_url = "https://api.paypal.com/v1/payments/payment"        
        
        access_token = self.token_card_id.acquirer_id.paypal_api_access_token
        card_partner = self.partner_id
        payload = {
            'intent': 'sale',
            'payer':  {
                "payment_method": "credit_card",
                "funding_instruments": [{
                    "credit_card_token": {
                        "credit_card_id": str(self.token_card_id.acquirer_ref),
                        "payer_id": "res_partner_" + str(card_partner.id)
                    }
                }]
             },
             'transactions': [{
                 'amount':{
                     'total': '{0:.2f}'.format(self.amount),
                     'currency': str(self.token_card_id.partner_id.company_id.currency_id.name)
                 },
                 'description': self.communication.encode("UTF-8")
             }]
        }        
        
        data = json.dumps(payload)
        headers = headers={"Content-Type": "application/json", "Authorization": "Bearer " + access_token}
        
        response_string = requests.post(base_url, data=data, headers=headers)
        
        
        _logger.error(response_string.text.encode('utf-8'))
        json_ob = json.loads(response_string.text)
        if 'id' in json_ob:
            return json_ob
        else:
            error_string = ""
            
            for paypal_error in json_ob['details']:
                error_string += paypal_error['issue'] + "\n"
            
            raise UserError(error_string)    