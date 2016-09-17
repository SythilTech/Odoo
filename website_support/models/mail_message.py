# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class MailMessageSupport(models.Model):

    _inherit = "mail.message"
    
    @api.model
    def create(self, values):
        new_rec = super(MailMessageSupport, self).create(values)
        
        #Reply messages to support tickets
        if new_rec.model == "website.support.ticket" and new_rec.message_type == "email" and new_rec.parent_id:

            #(Depreciated) Add to message history field for back compatablity
            self.env['website.support.ticket.message'].create({'ticket_id': new_rec.res_id, 'content':new_rec.body})

	    customer_replied = self.env['ir.model.data'].get_object('website_support','website_ticket_state_customer_replied')
            self.env['website.support.ticket'].browse(new_rec.res_id).state = customer_replied.id
            
        return new_rec