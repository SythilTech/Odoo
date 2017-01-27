# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResDatingEventFeedback(models.Model):

    _name = "res.dating.event.feedback"

    partner_id = fields.Many2one('res.partner', string="Partner")
    event_id = fields.Many2one('event.event', string="Event")
    event_feedback = fields.Text(string="Event Feedback")
    event_feedback_rating = fields.Integer(string="Event Rating")
    venue_id = fields.Many2one('res.partner', string="Venue")
    venue_feedback = fields.Text(string="Venue Feedback")
    venue_feedback_rating = fields.Integer(string="Venue Rating")
    reg_id = fields.Many2one('event.registration', string="Registrant")