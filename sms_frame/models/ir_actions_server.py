# -*- coding: utf-8 -*-
from openerp import api, fields, models

class IrActionsServer(models.Model):

    _inherit = 'ir.actions.server'
    
    sms_template_id = fields.Many2one('sms.template',string="SMS Template")

    @api.model
    def _get_states(self):
        res = super(IrActionsServer, self)._get_states()
        res.insert(0, ('sms', 'Send SMS'))
        return res

    @api.model
    def run_action_sms(self, action, eval_context=None):
        if not action.sms_template_id:
            return False
        self.env['sms.template'].send_sms(action.sms_template_id.id, self.env.context.get('active_id'))
        return False
