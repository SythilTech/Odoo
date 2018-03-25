# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ResPartnerCustomFields(models.Model):

    _inherit = "res.partner"
    
    @api.multi
    def open_custom_field_form(self):
        my_model = self.env['ir.model'].search([('model','=','res.partner')])[0]
        custom_model_view = self.env['ir.model.data'].sudo().get_object('crm_custom_fields','ir_model_view_form_custom_crm_fields')

        return {
	    'type': 'ir.actions.act_window',
	    'view_type': 'form',
	    'view_mode': 'form',
	    'res_model': 'ir.model',
	    'res_id': my_model.id,
            'view_id': custom_model_view.id,
	    'target': 'new',
        }