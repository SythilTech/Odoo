# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models

class ResUsersVoip(models.Model):

    _inherit = "res.users"
        
    @api.multi
    def create_voip_room(self):
        self.ensure_one()
        new_room = self.env['voip.room'].create({})
        
        #Add the current user as participant 1
        new_room.partner_ids = [(4,self.env.user.partner_id.id)]

        #Add the selected user as participant 2        
        new_room.partner_ids = [(4,self.partner_id.id)]
        
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': "/voip/window?room=" + str(new_room.id)
        }
