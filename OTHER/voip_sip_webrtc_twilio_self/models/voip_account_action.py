# -*- coding: utf-8 -*-
from openerp import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class VoipAccountActionInheritTwilio(models.Model):

    _inherit = "voip.account.action"

    call_user_ids = fields.Many2many('res.users', string="Call Users")
    
    def _voip_action_call_users(self, session, data):
        for call_user in self.call_user_ids:
            _logger.error("Call User " + call_user.name)