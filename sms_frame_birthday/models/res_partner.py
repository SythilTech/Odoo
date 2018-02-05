# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class ResPartnerSmsBirthday(models.Model):

    _inherit = "res.partner"

    birth_day = fields.Date(string="Birth Day")
    
    @api.model
    def send_birthday_sms(self):
        _logger.error("birthday")
        
        #Turn the queue manager on
	sms_queue = self.env['ir.model.data'].get_object('sms_frame', 'sms_queue_check')
        sms_queue.sudo().write({'active': True})
            
        for birthday_partner in self.env['res.partner'].search([('birth_day','=', fields.Date.today() )]):
            _logger.error("Send birthday: " + str(birthday_partner.name) )
            birthday_sms_template = self.env['ir.model.data'].get_object('sms_frame_birthday', 'sms_birthday_template')            
            self.env['sms.template'].send_sms(birthday_sms_template.id, birthday_partner.id)