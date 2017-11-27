# -*- coding: utf-8 -*-
from openerp import api, fields, models

class IrActionsServer(models.Model):

    _inherit = 'ir.actions.server'
    
    voip_call_template_id = fields.Many2one('voip.call.template',string="VOIP Call Template")

    @api.model
    def _get_states(self):
        res = super(IrActionsServer, self)._get_states()
        res.insert(0, ('voip_call', 'Make Voip Call'))
        return res

    @api.model
    def run_action_voip_call(self, action, eval_context=None):
        if not action.voip_call_template_id:
            return False
            
        action.voip_call_template_id.make_call(self.env.context.get('active_id'))
        
        return False
