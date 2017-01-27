# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from random import randint

from openerp import api, fields, models

class ResParnterDatingEvent(models.Model):

    _inherit = "res.partner"

    dating_event_location = fields.Boolean(string="Dating Venue")
    venue_feedback_ids = fields.One2many('res.dating.event.feedback', 'venue_id', string="Venue Feedback")
    dating_feedback_ids = fields.One2many('res.dating.event.feedback', 'partner_id', string="Dating Feedback")