# -*- coding: utf-8 -*-
from openerp import api, fields, models

class SmsMessageLead(models.Model):

    _inherit = "sms.message"

    def find_owner_model(self, sms_message):
        """Gets the model and record this sms is meant for"""
        #look for a partner with this number
        partner_id = self.env['res.partner'].search([('mobile','=', sms_message.find('From').text)])
        if len(partner_id) > 0:
            return {'record_id': partner_id[0], 'target_model': "res.partner"}
        else:
            lead_id = self.env['crm.lead'].search([('mobile','=', sms_message.find('From').text)])
            if len(lead_id) > 0:
                return {'record_id': lead_id[0], 'target_model': "crm.lead"}
            else:
                #Create a lead if you can't find a partner or lead
                record_id = self.env['crm.lead'].create({'name': 'Mobile Lead (' + str(sms_message.find('From').text) + ")", 'mobile':sms_message.find('From').text})
                return {'record_id': record_id, 'target_model': "crm.lead"}