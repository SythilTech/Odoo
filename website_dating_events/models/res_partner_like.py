# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerLikeEvent(models.Model):

    _inherit = "res.partner.like"

    event_id = fields.Many2one('event.event', string="Event")