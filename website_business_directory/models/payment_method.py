# -*- coding: utf-8 -*-
import json
import requests
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class PaymentMethodToken(models.TransientModel):

    _inherit = "payment.method"
    
    @api.multi
    def open_payment_token_wizard(self):
        return {
            'name': "Credit Card Payment Token",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'payment.method.token.wizard',
            'target': 'new',
            'context': {'default_payment_method_id': self.id},
        }
        
    @api.multi
    def open_token_charge_wizard(self):
        return {
            'name': "Credit Card Charge Token",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'payment.method.charge.wizard',
            'target': 'new',
            'context': {'default_payment_method_id': self.id},
        }