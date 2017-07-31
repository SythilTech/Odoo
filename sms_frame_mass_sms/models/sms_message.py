# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SmsMessageMass(models.Model):

    _inherit = "sms.message"
    
    mass_sms_id = fields.Many2one('sms.mass', string="Mass SMS")
    
    @api.model
    def create(self, vals):
        
        if vals['direction'] == "I" and vals['sms_content'] == "STOP":
            self.env['res.partner'].browse( int(vals['record_id']) ).sms_opt_out = True

        if vals['direction'] == "I" and vals['sms_content'] == "START":
            self.env['res.partner'].browse( int(vals['record_id']) ).sms_opt_out = False
            
        return super(SmsMessageMass, self).create(vals)
