# -*- coding: utf-8 -*

from odoo.addons.bus.controllers.main import BusController
from odoo.http import request

class VoipTwilioBusController(BusController):
    # --------------------------
    # Extends BUS Controller Poll
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:

            #Triggers the voip javascript client to start the call
            channels.append((request.db, 'voip.twilio.start', request.env.user.partner_id.id))
            
        return super(VoipTwilioBusController, self)._poll(dbname, channels, last, options)
