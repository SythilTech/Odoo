# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentToken(models.Model):

    _inherit = "payment.token"

    def make_charge(self, reference, amount, **kwargs):
        _logger.error("Make Charge")

        currency = self.partner_id.currency_id

        tx = self.env['payment.transaction'].sudo().create({
            'amount': amount,
            'acquirer_id': self.acquirer_id.id,
            'type': 'server2server',
            'currency_id': currency.id,
            'reference': reference,
            'payment_token_id': self.id,
            'partner_id': self.partner_id.id,
            'partner_country_id': self.partner_id.country_id.id,
        })

        try:
            tx.s2s_do_transaction(**kwargs)
            return True
        except:
            _logger.error('Error while making an automated payment')
            return False