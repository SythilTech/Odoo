from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime

class actions_server(models.Model):

    _inherit = 'ir.actions.server'
    
    sms_template_id = fields.Many2one('esms.templates',string="SMS Template")

    @api.model
    def _get_states(self):
        res = super(actions_server, self)._get_states()
        res.insert(0, ('sms', 'Send SMS'))
        return res

    @api.model
    def run_action_sms(self, action, eval_context=None):
        if not action.sms_template_id:
            return False
        self.env['esms.templates'].send_template(action.sms_template_id.id, self.env.context.get('active_id'))
        return False
