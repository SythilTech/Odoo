# -*- coding: utf-8 -*

from odoo.addons.bus.controllers.main import BusController
from odoo.http import request


class VoipBusController(BusController):
    # --------------------------
    # Extends BUS Controller Poll
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:

            #Callee receives notication asking to accept or reject the call plus media permission, Caller receives a notification showing how much time left before call is missed
            channels.append((request.db, 'voip.notification', request.env.user.partner_id.id))
            
            #Both the caller and callee are notified if the call is accepted, rejected or the call is ended early by the caller, the voip window then shows
            channels.append((request.db, 'voip.response', request.env.user.partner_id.id))
                        
            #Season Description Procotol
            channels.append((request.db, 'voip.sdp', request.env.user.partner_id.id))
            
            #ICE
            channels.append((request.db, 'voip.ice', request.env.user.partner_id.id))

            #End the call
            channels.append((request.db, 'voip.end', request.env.user.partner_id.id))
            
        return super(VoipBusController, self)._poll(dbname, channels, last, options)
