# -*- coding: utf-8 -*-
from openerp import api, fields, models

class ErdMakerModule(models.TransientModel):

    _name = "erd.maker.module"
    
    my_module = fields.Many2one('ir.module.module', required='True', string='Select Module', domain="[('state','=','installed')]")
    omit_builtin_fields = fields.Boolean(string="Omit Builtin Fields", default="True")
    output_text = fields.Html(string="Output HTML")
    table_count = 0
    table_dict = {}
 
    @api.one
    def make_erd_html(self):
        
        #find all models that are apart of this module
        for my_model in self.env['ir.model'].search([]):
            for module_item in my_model.modules.split(","):
                if module_item.strip() == self.my_module.name:
                    self.erd_html(my_model.model)
                
        temp_string = ""
        temp_string += "<style>\n"
        temp_string += "table {margin:50px;width:100%;border-collapse: collapse;}\n"
        temp_string += "th, td {border: 1px solid black;padding:5px;}\n"
        temp_string += "</style>\n"
        
        for keys,values in self.table_dict.items():
            temp_string += values.encode('utf-8')
        
        self.output_text = temp_string
        
        self.table_dict.clear()
        
        
    def erd_html(self, trans_model):
        table_output_string = ""
        table_output_string += "<a name=\"" + str(trans_model) + "\"></a>"
        table_output_string += "<table style=\"margin:50px;width:100%;border-collapse: collapse;\">\n"
        table_output_string += "<tr><th colspan=\"3\" style=\"border: 1px solid black;padding:5px;text-align:center;\">" + trans_model + "</th></tr>\n"
        table_output_string += "<tr><th style=\"border: 1px solid black;padding:5px;\">Name</th><th style=\"border: 1px solid black;padding:5px;\">Type</th><th style=\"border: 1px solid black;padding:5px;\">Label</th></tr>\n"
        
        for field in self.env['ir.model.fields'].search([('model_id.model','=',trans_model)]):

	    if self.omit_builtin_fields == True and (field.name == "id" or field.name == "display_name" or field.name == "create_date" or field.name == "create_uid" or field.name == "__last_update" or field.name == "write_date" or field.name == "write_uid"):
	        continue

	    field_name = field.name

	    if field.ttype == "many2one" or field.ttype == "one2many":
	        field_name += " <a href=\"#" + str(field.relation) + "\">(" + str(field.relation) + ")</a>"

	    if field.required == True:
	        field_name += "*"

	    table_output_string += "<tr><td style=\"border: 1px solid black;padding:5px;\">" + field_name + "</td><td style=\"border: 1px solid black;padding:5px;\">" + field.ttype + "</td><td style=\"border: 1px solid black;padding:5px;\">" + field.field_description + "</td></tr>\n"

        table_output_string += "</table>\n"
        self.table_dict[trans_model] = table_output_string
                
