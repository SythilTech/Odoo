# -*- coding: utf-8 -*-
from datetime import datetime
from urllib import urlencode, quote as quote
import logging
_logger = logging.getLogger(__name__)
import openerp
from openerp import tools, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta

from openerp import api, fields, models, tools

class CalendarAlarmManagerSms(models.Model):

    _inherit = "calendar.alarm_manager"

    @api.v7
    def do_notif_reminder(self, cr, uid, alert, context=None):
        _logger.error("do_notif_reminder")
        alarm = self.pool['calendar.alarm'].browse(cr, uid, alert['alarm_id'], context=context)
        event = self.pool['calendar.event'].browse(cr, uid, alert['event_id'], context=context)

        if alarm.type == 'notification':
            message = event.display_time

            delta = alert['notify_at'] - datetime.now()
            delta = delta.seconds + delta.days * 3600 * 24

            return {
                'event_id': event.id,
                'title': event.name,
                'message': message,
                'timer': delta,
                'notify_at': alert['notify_at'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            }
        elif alarm.type == 'sms':
            _logger.error("do_notif_reminder sms")
            message = event.display_time

            delta = alert['notify_at'] - datetime.now()
            delta = delta.seconds + delta.days * 3600 * 24

            return {
                'event_id': event.id,
                'title': event.name,
                'message': message,
                'timer': delta,
                'notify_at': alert['notify_at'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            }

    @api.v7
    def get_next_notif(self, cr, uid, context=None):
        _logger.error("get_next_notif")

        ajax_check_every_seconds = 300
        partner = self.pool['res.users'].read(cr, SUPERUSER_ID, uid, ['partner_id', 'calendar_last_notif_ack'], context=context)
        all_notif = []

        if not partner:
            return []

        all_events = self.get_next_potential_limit_alarm(cr, uid, ajax_check_every_seconds, partner_id=partner['partner_id'][0], mail=False, context=context)

        for event in all_events:  # .values()
            max_delta = all_events[event]['max_duration']
            curEvent = self.pool.get('calendar.event').browse(cr, uid, event, context=context)
            if curEvent.recurrency:
                bFound = False
                LastFound = False
                for one_date in self.pool.get("calendar.event").get_recurrent_date_by_event(cr, uid, curEvent, context=context):
                    in_date_format = one_date.replace(tzinfo=None)
                    LastFound = self.do_check_alarm_for_one_date(cr, uid, in_date_format, curEvent, max_delta, ajax_check_every_seconds, after=partner['calendar_last_notif_ack'], mail=False, context=context)
                    if LastFound:
                        for alert in LastFound:
                            all_notif.append(self.do_notif_reminder(cr, uid, alert, context=context))
                        if not bFound:  # if it's the first alarm for this recurrent event
                            bFound = True
                    if bFound and not LastFound:  # if the precedent event had alarm but not this one, we can stop the search fot this event
                        break
            else:
                in_date_format = datetime.strptime(curEvent.start, DEFAULT_SERVER_DATETIME_FORMAT)
                LastFound = self.do_check_alarm_for_one_date(cr, uid, in_date_format, curEvent, max_delta, ajax_check_every_seconds, after=partner['calendar_last_notif_ack'], mail=False, context=context)
                if LastFound:
                    for alert in LastFound:
                        all_notif.append(self.do_notif_reminder(cr, uid, alert, context=context))
        return all_notif

    @api.v7
    def get_next_mail(self, cr, uid, context=None):
        _logger.error("get_next_mail")
        now = openerp.fields.Datetime.to_string(datetime.now())

        icp = self.pool['ir.config_parameter']
        last_notif_mail = icp.get_param(cr, SUPERUSER_ID, 'calendar.last_notif_mail', default=False) or now

        try:
            cron = self.pool['ir.model.data'].get_object(cr, SUPERUSER_ID, 'calendar', 'ir_cron_scheduler_alarm', context=context)
        except ValueError:
            _logger.error("Cron for " + self._name + " can not be identified !")
            return False

        interval_to_second = {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }

        if cron.interval_type not in interval_to_second.keys():
            _logger.error("Cron delay can not be computed !")
            return False

        cron_interval = cron.interval_number * interval_to_second[cron.interval_type]

        all_events = self.get_next_potential_limit_alarm(cr, uid, cron_interval, notif=False, context=context)

        for curEvent in self.pool.get('calendar.event').browse(cr, uid, all_events.keys(), context=context):
            _logger.error(curEvent.name)
            max_delta = all_events[curEvent.id]['max_duration']

            if curEvent.recurrency:
                at_least_one = False
                last_found = False
                for one_date in self.pool.get('calendar.event').get_recurrent_date_by_event(cr, uid, curEvent, context=context):
                    in_date_format = one_date.replace(tzinfo=None)
                    last_found = self.do_check_alarm_for_one_date(cr, uid, in_date_format, curEvent, max_delta, 0, after=last_notif_mail, notif=False, missing=True, context=context)
                    for alert in last_found:
                        self.do_mail_reminder(cr, uid, alert, context=context)
                        at_least_one = True  # if it's the first alarm for this recurrent event
                    if at_least_one and not last_found:  # if the precedent event had an alarm but not this one, we can stop the search for this event
                        break
            else:
                _logger.error("non cur")
                in_date_format = datetime.strptime(curEvent.start, DEFAULT_SERVER_DATETIME_FORMAT)
                last_found = self.do_check_alarm_for_one_date(cr, uid, in_date_format, curEvent, max_delta, 0, after=last_notif_mail, notif=False, missing=True, context=context)
                for alert in last_found:
                    _logger.error("alarm")
                    self.do_mail_reminder(cr, uid, alert, context=context)
        icp.set_param(cr, SUPERUSER_ID, 'calendar.last_notif_mail', now)

    @api.v7
    def do_check_alarm_for_one_date(self, cr, uid, one_date, event, event_maxdelta, in_the_next_X_seconds, after=False, notif=True, mail=True, missing=False, context=None, sms=True):
        # one_date: date of the event to check (not the same that in the event browse if recurrent)
        # event: Event browse record
        # event_maxdelta: biggest duration from alarms for this event
        # in_the_next_X_seconds: looking in the future (in seconds)
        # after: if not False: will return alert if after this date (date as string - todo: change in master)
        # missing: if not False: will return alert even if we are too late
        # notif: Looking for type notification
        # mail: looking for type email

        res = []
        _logger.error("do_check_alarm_for_one_date")

        # TODO: replace notif and email in master by alarm_type + remove event_maxdelta and if using it
        alarm_type = []
        if notif:
            alarm_type.append('notification')
        if mail:
            alarm_type.append('email')
        if sms:
            _logger.error("sms alarm type")
            alarm_type.append('sms')

        if one_date - timedelta(minutes=(missing and 0 or event_maxdelta)) < datetime.now() + timedelta(seconds=in_the_next_X_seconds):  # if an alarm is possible for this date
            _logger.error("if alarm")
            for alarm in event.alarm_ids:
                _logger.error(alarm.name)
                if alarm.type in alarm_type and \
                    one_date - timedelta(minutes=(missing and 0 or alarm.duration_minutes)) < datetime.now() + timedelta(seconds=in_the_next_X_seconds) and \
                        (not after or one_date - timedelta(minutes=alarm.duration_minutes) > openerp.fields.Datetime.from_string(after)):
                        _logger.error(alarm.type)
                        alert = {
                            'alarm_id': alarm.id,
                            'event_id': event.id,
                            'notify_at': one_date - timedelta(minutes=alarm.duration_minutes),
                        }
                        res.append(alert)
        return res

    @api.v7
    def get_next_potential_limit_alarm(self, cr, uid, seconds, notif=True, mail=True, partner_id=None, context=None, sms=True):
        _logger.error("get_next_potential_limit_alarm")
        res = {}
        base_request = """
                    SELECT
                        cal.id,
                        cal.start - interval '1' minute  * calcul_delta.max_delta AS first_alarm,
                        CASE
                            WHEN cal.recurrency THEN cal.final_date - interval '1' minute  * calcul_delta.min_delta
                            ELSE cal.stop - interval '1' minute  * calcul_delta.min_delta
                        END as last_alarm,
                        cal.start as first_event_date,
                        CASE
                            WHEN cal.recurrency THEN cal.final_date
                            ELSE cal.stop
                        END as last_event_date,
                        calcul_delta.min_delta,
                        calcul_delta.max_delta,
                        cal.rrule AS rule
                    FROM
                        calendar_event AS cal
                        RIGHT JOIN
                            (
                                SELECT
                                    rel.calendar_event_id, max(alarm.duration_minutes) AS max_delta,min(alarm.duration_minutes) AS min_delta
                                FROM
                                    calendar_alarm_calendar_event_rel AS rel
                                        LEFT JOIN calendar_alarm AS alarm ON alarm.id = rel.calendar_alarm_id
                                WHERE alarm.type in %s
                                GROUP BY rel.calendar_event_id
                            ) AS calcul_delta ON calcul_delta.calendar_event_id = cal.id
             """

        filter_user = """
                RIGHT JOIN calendar_event_res_partner_rel AS part_rel ON part_rel.calendar_event_id = cal.id
                    AND part_rel.res_partner_id = %s
        """

        #Add filter on type
        type_to_read = ()
        if notif:
            type_to_read += ('notification',)
        if mail:
            type_to_read += ('email',)
        if sms:
            type_to_read += ('sms',)

        tuple_params = (type_to_read,)

        # ADD FILTER ON PARTNER_ID
        if partner_id:
            base_request += filter_user
            tuple_params += (partner_id, )

        #Add filter on hours
        tuple_params += (seconds,)

        cr.execute("""SELECT *
                        FROM ( %s WHERE cal.active = True ) AS ALL_EVENTS
                       WHERE ALL_EVENTS.first_alarm < (now() at time zone 'utc' + interval '%%s' second )
                         AND ALL_EVENTS.last_event_date > (now() at time zone 'utc')
                   """ % base_request, tuple_params)

        for event_id, first_alarm, last_alarm, first_meeting, last_meeting, min_duration, max_duration, rule in cr.fetchall():
            res[event_id] = {
                'event_id': event_id,
                'first_alarm': first_alarm,
                'last_alarm': last_alarm,
                'first_meeting': first_meeting,
                'last_meeting': last_meeting,
                'min_duration': min_duration,
                'max_duration': max_duration,
                'rrule': rule
            }

        return res

    @api.v7
    def do_mail_reminder(self, cr, uid, alert, context=None):
        _logger.error("do_mail_reminder")
        if context is None:
            context = {}
        res = False
        
        event = self.pool['calendar.event'].browse(cr, uid, alert['event_id'], context=context)
        alarm = self.pool['calendar.alarm'].browse(cr, uid, alert['alarm_id'], context=context)

        if alarm.type == 'email':
            res = self.pool['calendar.attendee']._send_mail_to_attendees(
                cr,
                uid,
                [att.id for att in event.attendee_ids],
                email_from=event.user_id.partner_id.email,
                template_xmlid='calendar_template_meeting_reminder',
                force=True,
                context=context
            )
        elif alarm.type == "sms":
            _logger.error("type sms")
            self.pool['sms.alarm'].send_sms_to_attendees(cr,uid,event,context=context)

        return res

