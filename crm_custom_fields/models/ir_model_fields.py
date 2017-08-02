# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from openerp import api, fields, models

class IrModelFieldsCRMFields(models.Model):

    _inherit = "ir.model.fields"
    
    custom_model_id = fields.Many2one('ir.model', string="Custom Model")
    crm_limited_types = fields.Selection([('char','Single Line Textbox'), ('text','Multi Line Textbox'), ('date','Date'), ('datetime','Date Time'), ('selection', 'Static Dropdown')], default="char", string="Field Type")
    crm_custom_name = fields.Char(string="Field Name")
    crm_custom_field = fields.Boolean(string="Custom CRM Field")
    crm_custom_field_widget = fields.Many2one('crm.custom.fields.widget', string="Widget")
    crm_custom_field_selection_ids = fields.One2many('ir.model.fields.selections', 'imf_id', string="Selection Options")
    
    @api.onchange('crm_limited_types')
    def _onchange_crm_limited_types(self):
        self.ttype = self.crm_limited_types
        
    @api.onchange('crm_custom_field_selection_ids')
    def _onchange_crm_custom_field_selection_ids(self):
        sel_string = ""
        for sel in self.crm_custom_field_selection_ids:
            sel_string += "('" + sel.internal_name + "','" + sel.name + "'), "
            
        self.selection = "[" + sel_string[:-2] + "]"
        
    @api.model
    def create(self, values):
        """Assign name when it's actually saved overwise they all get the same ID"""
        
        if 'crm_custom_field' in values:
            temp_name = "x_custom_" + values['field_description']
            temp_name = temp_name.replace(" ","_").lower()
            values['name'] = temp_name
            _logger.error(temp_name)
        
        return super(IrModelFieldsCRMFields, self).create(values)
        
class CrmCustomFieldsWidget(models.Model):

    _name = "crm.custom.fields.widget"

    name = fields.Char(string="Name")
    internal_name = fields.Char(string="Internal Name", help="The technicial name of the widget")

class IrModelFieldsCRMFieldsSelection(models.Model):

    _name = "ir.model.fields.selections"
    
    imf_id = fields.Many2one('ir.model.fields', string="Field")
    name = fields.Char(string="Name", required="True")
    internal_name = fields.Char(string="Internal Name", required="True")