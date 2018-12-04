# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class PaymentSubscription(models.Model):

    _name = "payment.subscription"

    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one('product.template', string="Product", required=True)
    initial_amount = fields.Float(string="Initial Amount", related="product_id.list_price")
    payment_acquirer_id = fields.Many2one('payment.acquirer', string="Payment Acquirer", domain="[('token_implemented','=',True), ('save_token','=','always')]", required=True)
    period_interval = fields.Selection([('days','Days')], default="days", string="Period Interval", required=True)
    period_amount = fields.Float(default="7.0", string="Period Amount", required=True)
    subscription_ids = fields.One2many('payment.subscription.subscriber', 'subscription_id', string="Subscribers")

class PaymentSubscriptionSubscriber(models.Model):

    _name = "payment.subscription.subscriber"

    subscription_id = fields.Many2one("payment.subscription", string="Subscription")
    partner_id = fields.Many2one('res.partner', string="Contact")
    status = fields.Selection([('inactive', 'Inactive'), ('active','Active')], string="Status")
    amount = fields.Float(string="Subscription Amount", help="The amount the subscriber agreed to when they subscribed")
    payment_token_id = fields.Many2one('payment.token', string="Payment Token")
    next_payment_date = fields.Datetime(string="Next Payment Date")

    @api.model
    def subscription_check(self):
        #Find all subscriptions where payment is due
        for subscriber in self.env['payment.subscription.subscriber'].search([('status', '=', 'active'), ('next_payment_date','<=',datetime.strftime( fields.datetime.now() , tools.DEFAULT_SERVER_DATETIME_FORMAT)) ]):            
            
            if subscriber.payment_token_id.make_charge(subscriber.subscription_id.name + " Subscripotion Payment", subscriber.amount, {}):
                # If success then move the next payment one peroid forward
                subscriber.next_payment_date = datetime.strptime(subscriber.next_payment_date, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=subscriber.subscription_id.period_amount)
            else:
                # On fail cancel the subscription
                subscriber.status = "inactive"