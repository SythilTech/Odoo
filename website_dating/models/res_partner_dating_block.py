# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerWebsiteDatingBlock(models.Model):

    _name = "res.partner.dating.block"
    _description = "Partner Dating Block"
    
    partner_id = fields.Many2one('res.partner', string="Partner")
    block_partner_id = fields.Many2one('res.partner', string="Block Partner")