# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerWebsiteDatingNotification(models.Model):

    _name = "res.partner.dating.notification"
    
    partner_id = fields.Many2one('res.partner', string="Partner")
    content = fields.Text(string="Content")
    ref_url = fields.Char(string="URL")
    has_read = fields.Boolean("Read")
