# -*- coding: utf-8 -*-
from openerp import api, fields, models

class IrModelCRMFields(models.Model):

    _inherit = "ir.model"
        
    
    custom_field_ids = fields.One2many('ir.model.fields', 'custom_model_id', string="Custom Fields", domain=[('crm_custom_field','=',True)])

    @api.one
    def fake_save(self):
        """Function does nothing, save gets called after"""
        pass

    @api.multi
    def write(self, values):
        
        ins = super(IrModelCRMFields, self).write(values)
        
        partner_custom_form_fields = self.env['ir.model.data'].sudo().get_object('crm_custom_fields', 'view_partner_form_inherit_crm_custom_fields')
        
        custom_form_fields_string = ""
        
        custom_form_fields_string += "<notebook position=\"inside\">\n"
        custom_form_fields_string += "    <page string=\"Custom Fields\">\n"
        custom_form_fields_string += "        <group>\n"
        
        for custom_field in self.env['ir.model.fields'].sudo().search([('crm_custom_field','=',True)]):
            custom_form_fields_string += "            <field name=\"" + str(custom_field.name) + "\""
            
            if custom_field.crm_custom_field_widget:
                custom_form_fields_string += " widget=\"" + custom_field.crm_custom_field_widget.internal_name + "\""
            
            custom_form_fields_string += "/>"
        
        custom_form_fields_string += "            <button name=\"open_custom_field_form\" type=\"object\" groups=\"sales_team.group_sale_manager\"  string=\"Add Custom Field\"/>\n"
        custom_form_fields_string += "        </group>\n"
        custom_form_fields_string += "    </page>\n"
        custom_form_fields_string += "</notebook>"

        partner_custom_form_fields.arch = custom_form_fields_string
        
        return ins