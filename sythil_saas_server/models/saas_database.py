# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from openerp import api, fields, models, tools
import openerp.http as http
from openerp.http import request
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import odoo
from odoo import api
from odoo import SUPERUSER_ID

import werkzeug

class SaasDatabase(models.Model):

    _name = "saas.database"
    
    partner_id = fields.Many2one('res.partner', string="Partner", help="Company that owns the data")
    state = fields.Selection([('trial', 'Trial'), ('subscribed','Subscribed'), ('canceled','Canceled')], string="State")
    trial_expiration = fields.Datetime(string="Trial Expiration Date")
    payment_method_id = fields.Many2one('payment.token', string="Payment Method")
    next_payment_date = fields.Datetime(string="Next Payment Date")
    subscription_cost = fields.Float(string="Subscription Cost")
    name = fields.Char(string="Database Name")
    login = fields.Char(string="Login")
    password = fields.Char(string="Password")
    super_admin_login = fields.Char(string="Admin Login")
    super_admin_password = fields.Char(string="Admin Password")
    template_database_id = fields.Many2one('saas.template.database', string="Template Database", ondelete="SET NULL")
    backup_ids = fields.One2many('ir.attachment', 'saas_database_id', string="Backups")
    user_id = fields.Many2one('res.users', string="SAAS User")
    access_url = fields.Char(string="Access URL", compute="_compute_access_url")
    domain_ids = fields.One2many('saas.database.domain', 'database_id', string="Domains")
    
    @api.depends('name')
    def _compute_access_url(self):
        system_redirect = self.env['ir.values'].get_default('saas.settings', 'system_redirect')
        
        if system_redirect == "db_filter" or system_redirect == False or system_redirect == "":
            self.access_url = "http://" + request.httprequest.host + "/web?db=" + self.name
        elif system_redirect == "subdomain":
            self.access_url = "http://" + self.name + "." + request.httprequest.host

    @api.multi
    def admin_login(self):
        self.ensure_one()
	request.session.authenticate(self.name, self.super_admin_login, self.super_admin_password)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.access_url,
        }
    
    @api.multi
    def user_login(self):
        self.ensure_one()
	request.session.authenticate(self.name, self.login, self.password)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.access_url,
        }
        
    @api.model
    def saas_subscription_check(self):
        #Find all databases where payment is due
        for saas_database in self.env['saas.database'].search([('state', '=', 'subscribed'), ('next_payment_date','<=',datetime.strftime( fields.datetime.now() , tools.DEFAULT_SERVER_DATETIME_FORMAT)) ]):            
            saas_database.payment_method_id.charge_card(saas_database.subscription_cost, saas_database.template_database_id.name + " Subscription")
            
            saas_database.next_payment_date = datetime.strptime(saas_database.next_payment_date, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(months=1)