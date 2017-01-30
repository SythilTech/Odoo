# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerWebsiteDatingLikes(models.Model):

    _name = "res.partner.dating.like"
    _description = "Partner Dating Like"
    
    partner_id = fields.Many2one('res.partner', string="Partner")
    like_partner_id = fields.Many2one('res.partner', string="Like Partner")
