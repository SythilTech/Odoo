# -*- coding: utf-8 -*-
from openerp import api, fields, models

class IrModelFieldsCRMFields(models.Model):

    _inherit = "ir.model.fields"
    
    custom_model_id = fields.Many2one('ir.model', string="Custom Model")
    crm_limited_types = fields.Selection([('char','Single Line Textbox'), ('text','Multi Line Textbox')], default="char" ,string="Field Type")
    crm_custom_name = fields.Char(string="Field Name")
    crm_custom_field = fields.Boolean(string="Custom CRM Field")

    @api.onchange('crm_custom_name')
    def _onchange_crm_custom_name(self):
        if self.crm_custom_name:
            self.field_description = self.crm_custom_name
            
            #Give temp name because it is required
            self.name = "x_" + str(self.env['ir.model.fields'].search_count([]) + 1)
        
    @api.onchange('crm_limited_types')
    def _onchange_crm_limited_types(self):
        self.ttype = self.crm_limited_types
        
    @api.model
    def create(self, values):
        """Assign name when it's actually saved overwise they all get the same ID"""
        new_ins = super(IrModelFieldsCRMFields, self).create(values)
        
        if new_ins.crm_custom_field:
            new_ins.name = "x_" + str(new_ins.id)
        
        return new_ins