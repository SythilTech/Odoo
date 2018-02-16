# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.exceptions import UserError

class ResPartnerXMPP(models.Model):

    _inherit = "res.partner"
    
    xmpp_address  = fields.Char(string="XMPP Address")
    
    @api.multi
    def xmpp_action(self):
        self.ensure_one()

        my_context = {'default_type': 'xmpp', 'default_model':'res.partner', 'default_record_id':self.id, 'default_to_address': self.xmpp_address, 'default_partner_id': self.id}        
        
        #Use the first XMPP account you find
        default_voip_account = self.env['xmpp.account'].search([])
        if default_voip_account:
            my_context['default_xmpp_account_id'] = default_voip_account[0].id
        else:
            raise UserError("No XMPP accounts found, can not send message")
           
        return {
            'name': 'XMPP Compose',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'voip.message.compose',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': my_context
         }