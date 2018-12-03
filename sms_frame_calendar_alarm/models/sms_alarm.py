# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, tools

class SMSAlarm(models.AbstractModel):

    _name = "sms.alarm"

    @api.model
    def send_sms_to_attendees(self,event):
        _logger.error("sms alarm")
        sms_template = self.env['ir.model.data'].get_object('sms_frame_calendar_alarm','sms_calendar_reminder')

        for attendee in event.partner_ids:
            sms_template.sms_to = attendee.mobile
            self.env['sms.template'].send_sms(sms_template.id, event.id)