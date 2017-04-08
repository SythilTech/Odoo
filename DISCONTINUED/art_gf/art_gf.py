from openerp import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
import random
import time

class art_gf(models.Model):

    _name = "art.gf"

    name = fields.Char(string="Name")
    gf_id = fields.Many2one('res.users', required=True, string="Girlfriend", domain="[('active','=',0),('art_gf','=',1)]")
    user_id = fields.Many2one('res.users', required=True, string="Assigned User", domain="[('art_gf','=',0)]")
    last_message_read = fields.Integer("Last Message Read")
    response_time = fields.Integer(string="Response Time", help="how many milliseconds before gf checks for message", default="6000")
    read_rate = fields.Integer(string="Read Rate", help="how many milliseconds it takes to read one character in a message", default="100")
    write_rate = fields.Integer(string="Write Rate", help="how many milliseconds it takes to read one character in a message", default="200")
    
    @api.model
    def random_talk(self):
        #get through each gf and send out a random message
        for gf in self.env['art.gf'].search([]):
            self.env['im_chat.presence'].sudo(gf.gf_id.id).update()
            gf.random_message()

    @api.one
    def analyze_message(self, message):
        #simulate delay because humans can't read and type messages in 5 milliseconds
        #time.sleep(self.response_time / 1000)
        
        #long messages take longer to read
        #time.sleep((len(message) * self.read_rate) / 1000)
        
        #perform complex calculation to create response message
        send_message = "love you too"
        
        #long message take longer to write
        #time.sleep((len(send_message) * self.write_rate) / 1000)
        
        #send the message
        self.gf_send_message(send_message)
    
    @api.one
    def random_message(self):
        prob = random.randint(0,100)
        
        if prob >= 0 and prob <= 10:
            pass
        if prob > 10 and prob <= 90:
            self.gf_send_message("love you baby")
        if prob > 90 and prob <= 100:
            self.gf_send_message("miss you")
    
    @api.one
    def gf_send_message(self, message):
        from_uid = self.gf_id.id
        
        user_to = self.user_id.id
        
        session_id = self.env['im_chat.session'].sudo(from_uid).session_get(user_to)['uuid']
        message_id = self.env['im_chat.message'].sudo(from_uid).post(from_uid, session_id, "message", message)

class im_chat_message(models.Model):
    _inherit = 'im_chat.message'
    
    @api.model
    def create(self, values):
        new_rec = super(im_chat_message, self).create(values)
        
        for gf in self.sudo().env['art.gf'].search([]):
            #from bf to the gf
	    if new_rec.from_id.id == gf.user_id.id and self.sudo().env['im_chat.session'].is_in_session(new_rec.to_id.uuid, gf.gf_id.id):
	        gf.analyze_message(new_rec.message)
        
        return new_rec
        