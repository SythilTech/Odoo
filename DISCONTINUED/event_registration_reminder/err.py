from openerp import models, fields, api
from datetime import datetime, timedelta
import openerp
import pytz
from pytz import timezone

import logging
_logger = logging.getLogger(__name__)

class err(models.Model):

    _name = "event.err"
 
    @api.v7
    def check_reminder(self, cr, uid, context=None):
        my_delta_time_ago = datetime.utcnow() + timedelta(minutes=120)
        
        #get all events that are going to start in 2 hours
        soon_events_ids = self.pool['event.event'].search(cr, uid, [('date_begin', '>', datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") ),('date_begin','<', my_delta_time_ago.strftime("%Y-%m-%d %H:%M:%S") )])
        
        soon_events = self.pool['event.event'].browse(cr, uid, soon_events_ids, context)
        
        email_templates_ids = self.pool['email.template'].search(cr, uid, [['name','=','Event Registrants Reminder']])
        email_templates = self.pool['email.template'].browse(cr, uid, email_templates_ids, context)
        
        for event in soon_events:
            
            for reg in event.registration_ids:
                if reg.reminded == False:
                
                
                    mail_values = self.pool['email.template'].generate_email(cr, uid, email_templates_ids[0], reg.id, context=context)
		    mail_values['email_to'] = reg.email
		
                    mail_obj = self.pool['mail.mail']
                    mail_id = mail_obj.create(cr, uid, mail_values)
                    mail_obj.send(cr, uid, mail_id)
                    reg.reminded = True
                
                
                
                
class err_reg(models.Model):

    _inherit = "event.registration"
    
    date_for_email = fields.Char(compute='_get_date_for_email', store=True, string="Date Formated")
    reminded = fields.Boolean()
    
    @api.one
    @api.depends('event_id.date_begin')
    def _get_date_for_email(self):
        utc = datetime.strptime(self.event_id.date_begin, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone('UTC'))
        to_zone = timezone(self.event_id.date_tz)
        meeting_date = utc.astimezone(to_zone)
        fmt = '%A, %d %B %Y %I:%M:%S%p %Z'
        self.date_for_email = meeting_date.strftime(fmt)