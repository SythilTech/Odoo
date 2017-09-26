# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
import odoo

from openerp import api, fields, models

class WebsiteSupportSettings(models.Model):

    _name = "website.support.settings"
    _inherit = 'res.config.settings'
            
    close_ticket_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="Close Ticket Email Template")

    #-----Close Ticket Email Template-----

    @api.multi
    def get_default_close_ticket_email_template_id(self, fields):
        return {'close_ticket_email_template_id': self.env['ir.values'].get_default('website.support.settings', 'close_ticket_email_template_id')}

    @api.multi
    def set_default_close_ticket_email_template_id(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'close_ticket_email_template_id', record.close_ticket_email_template_id.id)