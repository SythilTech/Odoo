from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class SmsMessage(models.Model):

    _name = "sms.message"
    _order = "my_date desc"
    
    record_id = fields.Integer(readonly=True, string="Record")
    account = fields.Many2one('sms.account', readonly=True, string="SMS Account")
    model = fields.Many2one('ir.model', readonly=True, string="Model")
    from_mobile = fields.Char(string="From Mobile", readonly=True)
    to_mobile = fields.Char(string="To Mobile", readonly=True)
    sms_content = fields.Text(string="SMS Message", readonly=True)
    record_name = fields.Char(string="Record Name", compute="_rec_nam")
    status_string = fields.Char(string="Response String", readonly=True)
    status_code = fields.Selection((('RECEIVED','Received'), ('failed', 'Failed to Send'), ('queued', 'Queued'), ('successful', 'Sent'), ('DELIVRD', 'Delivered'), ('EXPIRED','Timed Out'), ('UNDELIV', 'Undelivered')), string='Delivary State', readonly=True)
    sms_gateway_message_id = fields.Char(string="SMS Gateway Message ID", readonly=True)
    direction = fields.Selection((("I","INBOUND"),("O","OUTBOUND")), string="Direction", readonly=True)
    send_date = fields.Datetime(string="Send/Receive Date", readonly=True, help="The date and time the sms is received or sent")
 
 
    @api.one
    def send_sms()
        dtt
    
    @api.one
    @api.depends('to_mobile')
    def _rec_nam(self):
        if self.model != False and self.record_id != False:
            my_record_count = self.env[self.model_id.model].search_count([('id','=',self.record_id)])
            if my_record_count > 0:
                my_record = self.env[self.model.model].search([('id','=',self.record_id)])
                self.record_name = my_record.name
            else:
                self.record_name = self.to_mobile
