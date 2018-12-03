# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, tools

class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    def _get_default_sms_recipients(self):
        """ Method overriden from mail.thread (defined in the sms module).
            SMS text messages will be sent to attendees that haven't declined the event(s).
        """
        return self.mapped('attendee_ids').filtered(lambda att: att.state != 'declined').mapped('partner_id')

    def _do_sms_reminder(self):
        _logger.error("Do SMS Reminider")
        sms_template = self.env['ir.model.data'].get_object('sms_frame_calendar_alarm','sms_calendar_reminder')

        for event in self:
            for attendee in event.partner_ids:
                sms_template.sms_to = attendee.mobile
                self.env['sms.template'].send_sms(sms_template.id, event.id)