# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerDatingLikeEvent(models.Model):

    _inherit = "res.partner.dating.like"

    event_id = fields.Many2one('event.event', string="Event")